# Chunking comparison: development

| Decision | Winner | Status |
|---|---|---|
| Strategy | s0_lines_60_10 | S0 retained |

| Candidate | Repository Hit@5 loss | Repository MRR loss | Pooled MRR gain | Pooled mean cost | Pooled p95 cost | Qualifies |
|---|---:|---:|---:|---:|---:|---:|
| s1_lines_100_20 | True | True | True | True | False | False |
| s2_ast_v1 | True | False | False | True | True | False |
| s3_ast_v1_embed_text | True | False | False | True | True | False |

| Rule | Value |
|---|---:|
| max_cost_ratio_mean | 1.5 |
| max_cost_ratio_p95 | 1.5 |
| max_repo_hit5_loss | 1 |
| max_repo_mrr_loss | 0.03 |
| min_pooled_delta_mrr | 0.03 |
| tie_epsilon | 1e-09 |

| Repository | Strategy | Hit@1 | Hit@3 | Hit@5 | Span MRR | Mean cost | p95 cost | Coverage@5 | Density@5 | Top1 density | Test share |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| incidentweave | s0_lines_60_10 | 5/11 | 7/11 | 7/11 | 0.515152 | 7668.45 | 9727 | 0.636364 | 0.002750 | 0.008503 | 0.436364 |
| batch-processing-service | s0_lines_60_10 | 6/11 | 9/11 | 9/11 | 0.666667 | 8780.73 | 10855 | 0.920000 | 0.042942 | 0.133462 | 0.363636 |
| lifeos | s0_lines_60_10 | 8/11 | 10/11 | 11/11 | 0.821212 | 6375.27 | 8322 | 1.000000 | 0.038707 | 0.109375 | 0.000000 |
| incidentweave | s1_lines_100_20 | 5/11 | 8/11 | 10/11 | 0.636364 | 10839.18 | 14385 | 0.909091 | 0.002746 | 0.006545 | 0.327273 |
| batch-processing-service | s1_lines_100_20 | 6/11 | 9/11 | 10/11 | 0.684848 | 14200.00 | 16637 | 0.856000 | 0.024056 | 0.093051 | 0.381818 |
| lifeos | s1_lines_100_20 | 8/11 | 11/11 | 11/11 | 0.848485 | 7961.09 | 10569 | 1.000000 | 0.030727 | 0.076700 | 0.000000 |
| incidentweave | s2_ast_v1 | 4/11 | 7/11 | 8/11 | 0.522727 | 4525.18 | 7253 | 0.727273 | 0.005138 | 0.016064 | 0.272727 |
| batch-processing-service | s2_ast_v1 | 4/11 | 9/11 | 9/11 | 0.575758 | 4623.64 | 6620 | 0.464000 | 0.040730 | 0.097561 | 0.454545 |
| lifeos | s2_ast_v1 | 9/11 | 11/11 | 11/11 | 0.893939 | 4153.27 | 5827 | 1.000000 | 0.056957 | 0.285714 | 0.000000 |
| incidentweave | s3_ast_v1_embed_text | 5/11 | 8/11 | 8/11 | 0.560606 | 4334.64 | 7398 | 0.727273 | 0.005366 | 0.022523 | 0.200000 |
| batch-processing-service | s3_ast_v1_embed_text | 3/11 | 8/11 | 9/11 | 0.507576 | 4565.82 | 6620 | 0.440000 | 0.039035 | 0.085427 | 0.418182 |
| lifeos | s3_ast_v1_embed_text | 8/11 | 10/11 | 11/11 | 0.821212 | 3683.00 | 5827 | 1.000000 | 0.064437 | 0.316583 | 0.000000 |

| Strategy | Pooled Hit@1 | Pooled Hit@3 | Pooled Hit@5 | Pooled span MRR | Mean cost | p95 cost |
|---|---:|---:|---:|---:|---:|---:|
| s0_lines_60_10 | 19/33 | 26/33 | 27/33 | 0.667677 | 7608.15 | 10592 |
| s1_lines_100_20 | 19/33 | 28/33 | 31/33 | 0.723232 | 11000.09 | 16632 |
| s2_ast_v1 | 17/33 | 27/33 | 28/33 | 0.664141 | 4434.03 | 6620 |
| s3_ast_v1_embed_text | 16/33 | 26/33 | 28/33 | 0.629798 | 4194.48 | 6620 |

| Strategy | Wins | Losses | Ties | Exact sign-test p | Delta MRR | Bootstrap 95% interval |
|---|---:|---:|---:|---:|---:|---:|
| s1_lines_100_20 | 11 | 2 | 20 | 0.022461 | 0.055556 | [-0.022222, 0.128788] |
| s2_ast_v1 | 6 | 4 | 23 | 0.753906 | -0.003535 | [-0.120707, 0.113636] |
| s3_ast_v1_embed_text | 4 | 8 | 21 | 0.387695 | -0.037879 | [-0.169192, 0.101010] |

| Repository | Strategy | Fixture SHA-256 | Fixture bytes |
|---|---|---|---:|
| incidentweave | s0_lines_60_10 | 98e446a4ef5c312c45e5ff1f07bc89567be3a0687b2f8b5fc4d7ee72c01e416a | 244868 |
| incidentweave | s1_lines_100_20 | 00dbca7b8cddf31297cf84c16c2bc01783a9ed430b172f948d0f8bc44424c830 | 201227 |
| incidentweave | s2_ast_v1 | 2a2773cf284207319bead3ee2f65153d04b0598973793ca14c5182e67e47e63e | 318522 |
| incidentweave | s3_ast_v1_embed_text | c61fbc3084a8f692163b69179c1773e0f71a449bfd9179ada5743f24b769a224 | 318577 |
| batch-processing-service | s0_lines_60_10 | 71d32e142a0b92b648ea7c8c53e17bbbcbadfcbfc5ad745a87836e3b67dcab9e | 159548 |
| batch-processing-service | s1_lines_100_20 | 059d19690ad6390e4a776ec5600fb8279151c2dc800b9f2586b53930ed5246ef | 131427 |
| batch-processing-service | s2_ast_v1 | 29b7106ea229d81df10f9e63ad3187333e03db21f836f7dd067115664599e7f8 | 221686 |
| batch-processing-service | s3_ast_v1_embed_text | 5d2bfaf0ed8ad2ee460cd6c1af393f9a9f95be5067726186543dc15347f18aaf | 221804 |
| lifeos | s0_lines_60_10 | eff720d62f421d530843b1f3f803a19550d1edb93f0975494c75059c2c63b540 | 183993 |
| lifeos | s1_lines_100_20 | 7eaa232bc86c125582214647131ee1189d489b7b5fcc2aad7f26b055ffd88d0a | 160477 |
| lifeos | s2_ast_v1 | 873b220840e45b3d664e081bc1961e091dfbddfeb725525d46da94d52febabcf | 237127 |
| lifeos | s3_ast_v1_embed_text | e3ba61a582758cd72d96fea2e49e3863dd0917068357fea4107cfdc14ea85f07 | 237135 |
