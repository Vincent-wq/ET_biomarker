# -*- coding: utf-8 -*-
"""This is the utils library for the ET_biomarker project maintained by Qing Wang (Vincent)."
Functions:

"""
def add_pd_lr(data, var_list, sufix_str):
    """Create the left, right, and sum of the give var_list for a dataframe.
    
    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe which contains the var_list left and right part.
    var_list : :obj:`list` of :obj:`str`
        The list of labels without left or right specified.
    sufix_str : 'str'
        The string for left and right, e.g. Right or rh. etc.
    
    Returns
    -------
    data : pandas.DataFrame
        The dataframe which contains the var_list left, right and sum.
    res_list : :obj:`list` of :obj:`str`
        The newly added columns list.

    """
    left_suf = sufix_str[0]; right_suf = sufix_str[1];
    for x in var_list:
        data[x] = data[left_suf+x]+ data[right_suf+x];
    columns_left   = [ left_suf+x  for x in var_list];
    columns_right  = [ right_suf+x for x in var_list];
    res_list = var_list+columns_left+columns_right;
    return data, res_list

def ctr_by_nc(data, y_var, c_var, nc_group):
    """Remove the c_var effect by prediction from control group.
    
    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe which contains the y_var and c_var.
    y_var : :obj:`list` of :obj:`str`
        The list of target columns to control c_var for. 
    c_var : :obj:`str`
        The list of column for y_var to control by.
    nc_group : :obj:`str`
        The control group label.
    
    Returns
    -------
    dat : pandas.DataFrame
        The dataframe which contains the conlumns for y_var with c_var controled.
    new_col : :obj:`list` of :obj:`str`
        The newly added columns list (with c_var controled).
    reg_list : :obj:`list` of :obj:`str`
        The list of the regression models used.

    """
    from sklearn import linear_model
    import numpy as np
    if isinstance(c_var, str):
        n_x=1
    elif isinstance(c_var, list):
        n_x=len(c_var)
    else:
        n_x=0
    dat = data.copy(); n_all = dat.shape[0];
    nc_data = dat[dat['group'] == nc_group]; n_nc = nc_data.shape[0];
    x_nc = np.hstack((np.ones((n_nc,n_x)),  np.array(nc_data[c_var]).reshape(-1, n_x))); 
    x_all= np.hstack((np.ones((n_all,n_x)), np.array(dat[c_var]).reshape(-1, n_x)));
    reg_list = []; new_col=[];
    for x in y_var:
        reg = linear_model.LinearRegression()
        y_nc= np.array(nc_data[x]);
        reg.fit(x_nc, y_nc);
        if n_x>1:
            tmp_col = x+"_"+"_".join(c_var)
        else:
            tmp_col = x+"_"+c_var
        dat[tmp_col] = dat[x]-np.matmul(x_all, reg.coef_)
        new_col.append(tmp_col); reg_list.append(reg);
    return dat, new_col, reg_list

def ctr_tiv(data, y_var, icv_var, ctr_var, method_name):
    """Control the confounding effect with multiple methods: .
    
    Parameters
    ----------
    data : pandas.DataFrame
        The dataframe which contains all the needed columns: y_var, icv_var, ctr_var, and 'group'.
    y_var : :obj:`list` of :obj:`str`
        The list of columns (ROI volumnes) to be corrected. 
    icv_var : :obj:`str`
        The intracranial volumne column used to correct the y_var.
    ctr_var : :obj:`str`
        The confounding effect ctr_var will be corrected by prediction from control group.
    method_name : 'str'
        The method name for intracranial volumne correction:
        'dpa' : 
        'ppa' :
        'rm_norm' : 
        'asm' : 
    
    Returns
    -------
    dat : pandas.DataFrame
        The dataframe with corrected var_list colums added.
    res_list : :obj:`list` of :obj:`str`
        The newly added columns.

    """
    
    from sklearn import linear_model
    import numpy as np
    
    dat = data.copy(); n_all = dat.shape[0];
    print('Using ', method_name)
    if isinstance(ctr_var, str):
        comb_cvar=[icv_var, ctr_var]
    elif isinstance(ctr_var, list):
        comb_cvar=[icv_var]+ctr_var
    else:
        comb_cvar=[]
    
    if method_name == 'dpa': # direct proportion adjustment
        new_col=[];
        for x in y_var:
            r_name = x+'_dpa'; new_col.append(r_name);
            dat[r_name] = dat[x]/dat[icv_var];
        dat_, col_, reg_list_ = ctr_by_nc(dat, new_col, ctr_var, 'NC');
        res_col = new_col+col_;
        print('New columns', str(len(res_col))+' : ', res_col)
        return dat_, res_col
    
    if method_name == 'ppa': # power_corrected_portion
        reg_list = []; new_col=[];
        log_ctr  = np.log10(np.array(dat[icv_var]));
        x_mat    = np.hstack((np.ones((n_all, 1)), np.reshape(log_ctr, [n_all, 1])))
        for x in y_var:
            reg = linear_model.LinearRegression()
            y = np.log10(np.array(dat[x]));
            reg.fit(x_mat, y);
            tmp_col = x + "_ppa";
            dat[tmp_col] = dat[x]/np.power(dat[icv_var],reg.coef_[1])
            reg_list.append(reg); new_col.append(tmp_col);
        dat_, col_, reg_list_ = ctr_by_nc(dat, new_col, ctr_var, 'NC');
        res_col = new_col+col_;
        print('New columns', str(len(res_col))+' : ', res_col)
        return dat_, res_col
    
    if method_name == 'rm_norm': #residual based on n
        dat_, res_col, reg_list_ = ctr_by_nc(dat, y_var, comb_cvar, 'NC')
        print('New columns', str(len(res_col))+' : ', res_col)
        return dat_, res_col
    
    if method_name == 'asm': # allometric scaling coefficient (ASC)
        nc_data = dat[dat['group'] == 'NC']; n_nc = nc_data.shape[0]; 
        x_nc = np.log10(np.hstack((np.ones((n_nc,1)),  np.array(nc_data[icv_var]).reshape(-1, 1)))); 
        x_all= np.log10(np.hstack((np.ones((n_all,1)), np.array(dat[icv_var]).reshape(-1, 1))));
        reg_list = []; new_col=[];
        for x in y_var:
            reg = linear_model.LinearRegression()
            y_nc= np.log10(np.array(nc_data[x]));
            reg.fit(x_nc, y_nc);
            tmp_col = x+"_asm"
            dat[tmp_col] = np.log10(dat[x])-np.matmul(x_all[:,1:], reg.coef_[1:])
            reg_list.append(reg); new_col.append(tmp_col);
        dat_, col_, reg_list_ = ctr_by_nc(dat, new_col, ctr_var, 'NC');
        res_col = new_col+col_;
        print('New columns', str(len(res_col))+' : ', res_col)
        return dat_, res_col
    
    if method_name == 'wdcr':# whole dataset confound regression
        pass
    if method_name == 'propensity_score_matching':# whole dataset confound regression
        pass
    if method_name == 'ipsw':# whole dataset confound regression
        pass
    if method_name == 'counter_balancing':# whole dataset confound regression
        pass
    else:
        print([method_name, ' not supported...'])
        return data,[],[]
    return 1

def glm_test(data, tar_list, model_str):
    """Doing simple GLM model for tar_list in the dataframe and return the model as dicts.
    
    Parameters
    ----------
    data: pandas.DataFrame
    The dataframe which contains all the needed columns: tar_list.
    tar_list: :obj:`list` of :obj:`str`
    The list of dependent variables for the GLM model to test.
    model_str: :obj:`str`
    The GLM model string.
    
    Returns
    -------
    res_dict: :obj: dict of :obj: GLM models. Like: {tar_var:{'forluma': formula, 'res':res}}
    
    Example: 
    
    """

    res_dict={}
    for var_ in tar_list:
        res_dict[var_]={};
        formula = var_ +model_str
        mod = smf.glm(formula=formula, data=data)
        res = mod.fit()
        res_dict[var_ ] = {'formula':formula, 'res':res};
    return res_dict

def rep_model(glm_dict):
    """Reporting results from GLM models in glm_dict.
    
    Parameters
    ----------
    glm_dict: :obj: dict of :obj: 
    GLM models. Like: {tar_var:{'forluma': formula, 'res':res}}
    
    Returns
    -------
    Nothing.
        
    """
    for k in glm_dict.keys():
        print('\n')
        print(glm_dict[k]['formula'],'\n')
        print(glm_dict[k]['res'].rsquared)
        print(glm_dict[k]['res'].summary())
        print(glm_dict[k]['res'].summary2())
    return glm_dict

def cal_es(data, tar_list,  stats_cols, alpha, n_permu, method_name):
    """Calculate effect size Cohen's d with permutation test and wilcoxon ranksum test.
    
    Parameters
    ----------
    data: pandas.DataFrame
    The dataframe which contains all the needed columns: tar_list.
    
    """

    data_df = data.copy();  out_df= pd.DataFrame();
    
    for k in tar_list:
        sample_Pat = data_df[data_df['group'] == 'ET'][[k]]; sample_NC = data_df[data_df['group'] == 'NC'][[k]];
        if 'permu' in method_name:
            [val_permu, p_permu, samples] = permute_Stats(sample_Pat, sample_NC, 'cohen_d', alpha, n_permu, 0); 
            
        if 'rank_sum' in method_name:
            (val_ranksum, p_ranksum)=ranksums(sample_Pat, sample_NC);
            
        out_df=out_df.append(
        dict(zip(stats_cols, [k,'ETNC',val_permu, p_permu, val_ranksum, p_ranksum, method_name])), ignore_index=True);
    return out_df 

def permute_Stats(sample1, sample2, measure, alpha, reps, is_plot):
    """Calculate test statistics by permutation.
    
    Parameters
    ----------
    sample1: :obj: list
        test sample1.
    sample2: :obj: list
        test sample2.
    measure: :obj: string
        Test static, for example: Cohen's d. 
    alpha : float
        The significance level.
    reps: int
        Number of permutations.
    is_plot : boolean
        Flag to give a plot of permutation histogram.

    Returns
    -------
    test_stat : :obj: list
        The values of the test statistics.
    p_val : :obj: list
        The p-val of the test statistics.
    samples : 
        Permuation results.
        
    """
    import numpy as np
    np.random.seed(115)
    n1, n2 = map(len, (sample1, sample2));
    data = np.concatenate([sample1, sample2])
    ps = np.array([np.random.permutation(n1+n2) for i in range(reps)])
    xp = data[ps[:, :n1]]; yp = data[ps[:, n1:]]
    if measure == 'cohen_d':
        test_stat = cohen_d(sample1, sample2);
        samples = np.array([cohen_d(k, v) for k,v in zip(xp, yp)]);
    p_val = 2*np.sum(samples >= np.abs(test_stat))/reps;
    #print(measure+' : %.6f' % test_stat, ", p-value = %.6f " % p_val)
    if is_plot == 1:
        import matplotlib.pyplot as  plt
        fig = plt.figure()
        plt.hist(samples, 25, histtype='step')
        plt.axvline(test_stat, c='r')
        plt.axvline(np.percentile(samples, alpha/2), linestyle='--',c='r')
        plt.axvline(np.percentile(samples, 100-alpha/2), linestyle='--',c='r')
    return [test_stat, p_val, samples]

def cohen_d(d1, d2):
    # Cohen's d for independent samples with different sample sizes
    import numpy as np
    from math import sqrt
    d1 =np.array(d1); d2 =np.array(d2);
    n1, n2 = len(d1), len(d2) # calculate the size of samples
    s1, s2 = np.var(d1, ddof=1), np.var(d2, ddof=1) # calculate the variance of the samples
    s = sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2)) # calculate the pooled standard deviation
    u1, u2 = np.mean(d1), np.mean(d2) # calculate the means of the samples
    d_coh_val = (u1 - u2) / s; # calculate the effect size
    #print('Cohens d: %.3f' % d_coh_val)
    return d_coh_val


def reformat_df(df, group_name, es_name):
    import statsmodels.stats as sts
    method_name=df['method'].unique();
    voi_name=df[df.method=='covariate']['voi'].unique();
    es_list=[]; p_list=[]; p_multi_list=[];
    for x in method_name:
        es_list_= list(df[(df['group']==group_name)&(df['method']==x)][es_name[0]]);
        p_list_ = list(df[(df['group']==group_name)&(df['method']==x)][es_name[1]]);
        p_multi_list_=sts.multitest.multipletests(p_list_, alpha=alpha/100,
                                                  method='fdr_bh', is_sorted=False, returnsorted=False)[1];
        es_list.append(es_list_); p_list.append(p_list_); p_multi_list.append(p_multi_list_);
    return es_list, p_list, p_multi_list, voi_name, method_name