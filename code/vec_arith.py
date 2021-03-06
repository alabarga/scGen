from hf import *
import numpy as np
import scanpy.api as sc
import os
from data_reader import data_reader
import wget


# =============================== downloading training and validation files ====================================
# we do not use the validation data to apply vectroe arithmetics in gene expression space

train_path = "../data/train_kang.h5ad"
valid_path = "../data/valid_kang.h5ad"

if os.path.isfile(train_path):
    data = sc.read(train_path)
else:
    train_url = "https://drive.google.com/uc?export=download&id=1-RpxbXwXEJLYZDFSHnWYenojZ8TxRZsP"
    t_dl = wget.download(train_url, train_path)
    data = sc.read(train_path)

if os.path.isfile(valid_path):
    validation = sc.read(valid_path)
else:
    train_url = "https://drive.google.com/uc?export=download&id=1-RpxbXwXEJLYZDFSHnWYenojZ8TxRZsP"
    t_dl = wget.download(train_url, valid_path)
    validation = sc.read(valid_path)
# =============================== data gathering ====================================
#training cells
t_in = ['CD8T','NK','B','Dendritic', 'FCGR3A+Mono','CD14+Mono']
#heldout cells
t_out = [ 'CD4T']
dr = data_reader(data, validation,{"ctrl":"control", "stim":"stimulated"}, t_in, t_out)



train_real_cd = dr.train_real_adata[dr.train_real_adata.obs["condition"] == "control",:]
train_real_cd = dr.balancer(train_real_cd)
train_real_stimulated = dr.train_real_adata[dr.train_real_adata.obs["condition"] == "stimulated",:]
train_real_stimulated = dr.balancer(train_real_stimulated)
train_real_cd = train_real_cd.X
train_real_stimulated = train_real_stimulated.X


def predict(cd_x, hfd_x, cd_y):
    eq = min(len(cd_x), len(hfd_x))
    cd_ind = np.random.choice(range(len(cd_x)), size=eq, replace=False)
    stim_ind = np.random.choice(range(len(hfd_x)), size=eq, replace=False)
    cd = np.average(cd_x[cd_ind, :], axis=0)
    stim = np.average(hfd_x[stim_ind, :], axis=0)
    delta = stim - cd
    predicted_cells = delta + cd_y
    return predicted_cells



if __name__ == "__main__":
    sc.settings.figdir = "../results"
    adata_list = dr.extractor(data, "CD4T")
    ctrl_CD4T = adata_list[1]
    predicted_cells = predict(train_real_cd, train_real_stimulated, ctrl_CD4T.X.A)
    all_Data = sc.AnnData(np.concatenate([adata_list[1].X.A, adata_list[2].X.A, predicted_cells]))
    all_Data.obs["condition"] = ["ctrl"] * len(adata_list[1].X.A) + ["real_stim"] * len(adata_list[2].X.A) +\
                                ["pred_stim"] * len(predicted_cells)
    all_Data.var_names = adata_list[3].var_names
    dr.reg_mean_plot(all_Data, "../results/", "Vec_Arith ")
    dr.reg_var_plot(all_Data, "../results/", "Vec_Arith ")
    sc.pp.neighbors(all_Data)
    sc.tl.umap(all_Data)
    sc.pl.umap(all_Data, color=["condition"], save="Vec_Arith.pdf", show=False)
    sc.pl.violin(all_Data, groupby='condition', keys="ISG15", save="Vec_Arith.pdf", show=False)


