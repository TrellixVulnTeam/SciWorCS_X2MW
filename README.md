<p align="center">
  <img src="docs/Images/g7259.png" width="50%" title="CloneCognition">
</p>

# SciWorCS
[![Sponsors on Open Collective](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](#sponsors)
[![Backers on Open Collective](https://img.shields.io/badge/python-2.7-orange.svg?style=flat-square)](#backers)
[![Sponsors on Open Collective](https://img.shields.io/badge/debian-10+-blue.svg?style=flat-square)](#sponsors)
[![Sponsors on Open Collective](https://img.shields.io/badge/ubuntu-14.0%2B-yellow.svg?style=flat-square)](#sponsors)
[![Sponsors on Open Collective](https://img.shields.io/badge/server-linux-red.svg?style=flat-square)](#sponsors)
[![Sponsors on Open Collective](https://img.shields.io/badge/System-SWfMS-brightgreen.svg?style=flat-square)](#sponsors)



A number of Scientific Workflow Management Systems (SWfMSs) have been proposed and developed in recent years to facilitate the scientific experiments. For example some of the popular SWfMSs are: Taverna, Galaxy, Kepler, Pegasus, VisTrails, Triana, VIEW. The existing SWfMSs support only single user for a given data analysis process, however, modern scientific research projects are often collaborative in nature --involving multiple researchers of diverse domain and expertise. SciWorCS is a Collaborative Scientific Workflow management System. SciWorCS follows a plugin-based architecture for the scientific computational modules. It provides collaborative environment for scientific data analysis using efficient attribute level locking scheme. In addition to the collaborative data analysis, SciWorCS also provides real time monitoring of the computation steps.

<p align="center">
  <img src="https://i.imgur.com/RiHsokS.gif"  title="SciWorCS">
</p>



# Installation
Please make sure you have the following environment setups:

1. Python 2.7.
2. Flask Mircorframework (http://flask.pocoo.org/)
3. Apache CouchDB (http://couchdb.apache.org/)


# Usage Instructions
On Cloning and setting up the required environment for this project, you need to follow the speps below:

###### 1. Make sure in the project directory:
```
$cd SciWorCS
```

###### 3. Run the `main.py` script as following for starting SciWorCS:
```
$python main.py
```
<p align="center">
  <img src="https://i.imgur.com/BqfJcpo.gif"  title="SciWorCS">
</p>

On successfull installation, running the SciWorCS should display the workflow editor UI as illustrated in the following screenshot. 


**SciWorCS Panel A:** The panel labeled as 'A', contains all the workflow components such as Toolbox (i.e., set of workflow modules), Saved Workflows and Shared Workflows with other users. The set of modules are classified in different Toolbox based on the general data analysis purposes of the computational modules. Some examples of such Toolboxes are Bioinformatics, Machine Learning, Source Analysis and so on as illustrated in the figure.


**SciWorCS Panel B:** The collaborative composition of the workflow is done on panel 'B'. For the intended data analysis task, the required modules are selected from the corresponding Toolbox to appear in the composition panel. The selected modules are then connected together on the corresponding input/output ports for defining the datalink relation among the modules. 

**SciWorCS Panel C:** The modules can be configured with corresponding attributes from panel 'C'.

**SciWorCS Panel D:** Panel 'D' shows a list of collaborators and their current online/offline status. 

**SciWorCS Panel E:** The list of the workflow outputs is shown in panel 'E'. 

**SciWorCS Panel F:** A new dataset can be browsed and uploaded to the central server for analysis from the panel 'F'.


<p align="center">
  <img src="docs/Images/SciWorCS.jpg" width="95%" title="SciWorCS">
</p>
