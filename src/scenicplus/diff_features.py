# Getting DEGs
import anndata
import scanpy as sc
from typing import Union, Dict, Sequence, Optional, List
import logging
import pandas as pd
pd.options.mode.chained_assignment = None

def format_df(df, key, adjpval_thr, log2fc_thr):
    """
    A helper function to format differential test results
    """
    df.index = df['names']
    df = df[['logfoldchanges', 'pvals_adj']]
    df.columns = ['Log2FC', 'Adjusted_pval']
    df['Contrast'] = key
    df.index.name = None
    df = df.loc[df['Adjusted_pval'] <= adjpval_thr]
    df = df.loc[df['Log2FC'] >= log2fc_thr]
    df = df.sort_values(
        ['Log2FC', 'Adjusted_pval'], ascending=[False, True]
    )
    return df

def get_differential_features(scplus_obj: 'SCENICPLUS',
                             variable,
                             use_hvg: Optional[bool] = True,
                             contrast_type: Optional[List] = ['DARs', 'DEGs'],
                             adjpval_thr: Optional[float] = 0.05,
                             log2fc_thr: Optional[float] = np.log2(1.5)
                             ):
    
    """
    Get DARs of DEGs given reference variable. 
    
    Parameters
    ---------
    scplus_obj: `class::SCENICPLUS`
        A SCENICPLUS object.
    variable: str
        Variable to compute DARs/DEGs by (has to be included in scplus_obj.metadata_cell)
    contrast_type: list, optional
        Wheter to compute DARs and/or DEGs per variable
    """
    # Create logger
    level = logging.INFO
    log_format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
    handlers = [logging.StreamHandler(stream=sys.stdout)]
    logging.basicConfig(level=level, format=log_format, handlers=handlers)
    log = logging.getLogger('SCENIC+')
    
    for contrast in contrast_type:
        log.info('Calculating ' + contrast + ' for variable ' + variable)
        if contrast == 'DEGs':
            adata = anndata.AnnData(X=scplus_obj.X_EXP, obs=pd.DataFrame(index=scplus_obj.cell_names), var=pd.DataFrame(index=scplus_obj.gene_names))
        if contrast == 'DARs':
            adata = anndata.AnnData(X=scplus_obj.X_ACC.T, obs=pd.DataFrame(index=scplus_obj.cell_names), var=pd.DataFrame(index=scplus_obj.region_names))
        adata.obs = scplus_obj.metadata_cell
        sc.pp.log1p(adata)
        if use_hvg:
            sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
        sc.tl.rank_genes_groups(adata, variable, method='wilcoxon')
        groups = adata.uns['rank_genes_groups']['names'].dtype.names
        diff_dict = {group: format_df(sc.get.rank_genes_groups_df(adata, group=group), group, adjpval_thr, log2fc_thr) for group in groups}
        if contrast not in scplus_obj.uns.keys():
            scplus_obj.uns[contrast] = {} 
        scplus_obj.uns[contrast][variable] = diff_dict
        log.info('Finished calculating ' + contrast + ' for variable ' + variable)
