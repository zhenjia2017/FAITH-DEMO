
# FAITH: A Demonstration System for Faithful Temporal Question Answering

Description
------
This repo is for the FAITH demo. The video is available at [LINK](https://www.youtube.com/watch?v=O_kngz1S5zU).

Temporal question answering (TQA) aims to answer questions that involve temporal constraints or require temporal information. We propose Faith, a novel TQA approach that operates over heterogeneous sources and ensures explainable answers by presenting traceable and faithful evidence. In Faith, we design a new recursive answering mechanism transforming implicit temporal constraints into explicit conditions.Additionally, we visualize the system functionality to track how the answers are computed and the supporting evidence is derived. 

*Overview of the TQA pipeline*
<div style="text-align: center;"><img src="tqa-pipeline.png"  alt="overview" width=80%  /></div>


*Example demonstration*
<div style="text-align: center;"><img src="demo.png"  alt="overview" width=80%  /></div>


### Dependencies
TQA backend is based on our WWW'24 full paper "Faithful Temporal Question Answering over Heterogeneous Sources".

For more details see our paper: [Faithful Temporal Question Answering over Heterogeneous Sources](https://dl.acm.org/doi/10.1145/3589334.3645547) and visit our project website: https://faith.mpi-inf.mpg.de.


### Flask API
faith_api.py: Flask framework providing the API service.

### TQA backend
faith_backend.py: TQA backend main program.

### UI
The implementation scripts for UI are in the "ui" folder. 

## Feedback
Any feedback are welcome! Please contact us via mail: [zjia@swjtu.edu.cn](mailto:zjia@swjtu.edu.cn).