# ETL/Dashi (200824-1630)

Source: https://oicr-gsi.readthedocs.io/en/latest/infrastructure.html

ETL/Dashi (200824-1630)
View page source
ETL/Dashi (200824-1630)
Dashi (https://dashi.oicr.on.ca/) is an in-house dashboard based on Python’s Dash framework for visualizing sample QC metrics. GSI-QC-ETL (ETL) is a series of data handler scripts which ingests the output from QC workflow runs and formats the data into a tabular format amenable for plotting via Dashi. ETL scripts and Dashi updates are configured to run automatically via Olives as new data is processed.
Dimsum
Dimsum (https://dimsum.gsi.oicr.on.ca internal network access only) is an in-house developed dashboard that presents data from MISO, GSI-QC-ETL, and other OICR systems with the goal of streamlining quality control and other processes.
Djerba
Djerba (https://github.com/oicr-gsi/djerba) is an in-house application used by CGI interpreters to create WGTS, pWGS and TAR reports and facilitate interpretation.
Djerba is a command-line application, designed and written by CGI staff. Further documentation and technical guides for Djerba can be viewed on ReadTheDocs. The Djerba software includes mini-Djerba, a standalone application with a subset of Djerba functions, which can be used to update clinical report documents; see TM-003 Geneticist Sample Review and Sign-Off Procedure.
MISO (1.14+)
MISO is the in-house developed and maintained open-source LIMS software. MISO (https://miso.oicr.on.ca) is a Java application responsible for tracking all samples and the associated metadata from initial sample accessioning through to drafting of reports and delivery of data. MISO functionality is based on the concept of sample derivation and propagation as a sample moves through the laboratory lifecycle. The hierarchy of metadata is as follows:
Identity (donor)→Tissue →Sample → Library → Library Aliquot, where an arrow represents a parent→child relationship.
Library aliquots are then placed into sequencing pools which are customized according to the specifications of each individual sequencing unit (ie. Illumina flow cells and lanes). Propagation through the hierarchy of levels is strictly enforced by the user interface, and unique identifiers are automatically generated and recorded for each level in a SQL database. Multiple or subsequent samples received for a given donor would automatically generate incremented identifiers allowing cross-referencing between samples. These unique identifiers allow for automatic association of downstream bioinformatics data to the specific library, sample, tissue, and donor. The use of MISO is described in more detail in TM. LIMS Usage - MISO.
Modulator (0.1)
Modulator is a Python script for automatically building environment modules in the cluster environment (https://gitlab.oicr.on.ca/ResearchIT/modulator). Modulator reads .yaml configuration files containing the build “recipe”: a configuration of instructions which calls various functions for downloading and building bioinformatics software. Access to the resulting modules are controlled at the group level, allowing only users within the appropriate group the ability to load modules, including the production users ‘hsqwprod’ and ‘seqprodbio’. All recipes are version controlled, thus allowing for lockdown of the modules used for the production pipeline.
Pinery (2.13.0+)
Pinery (http://pinery.gsi.oicr.on.ca internal network access only) is a webservice which exposes the MISO data as an API to retrieve information about samples, libraries, runs, and other information recorded in the LIMS. Both file provenance and Shesmu (described below) use this system as a primary source of information.
Provenance Client (2.5.17+)
The Provenance Client is a command line application and library written in Java which retrieves sample provenance from Pinery and analysis provenance from Vidarr and combines it into file provenance. The library is also used directly by Shesmu, which is used to automate subsequent workflows and tasks.
Provenance records
Provenance records connect run, sample, and analysis metadata, therefore allowing one to trace all analysis for a given sample. The provenance records consist of three types of information. Note that each system is described in more detail below.
The three types of provenance include:
Sample provenance, provided by Pinery, which contains the information about samples captured in the MISO database.
Analysis provenance, provided by Vidarr, containing information regarding analysis metadata and files generated from the informatics pipeline workflows.
File provenance, generated as needed by the Provenance Client, combines LIMS and Analysis provenance to show the provenance (history and origin) of each file produced in analysis.
Each type of provenance has a unique key that allows it to be joined together and split apart.
Requisition system
The requisition system (https://requisition.genomics.oicr.on.ca/) is an external facing web application sample accessioning system for external collaborators submitting clinical samples to OICR. Details of the requisition system, including current version, are described in the QM. Requisition and Reporting System SOP. The requisition system contains all of the clinical metadata associated with samples submitted for clinical sequencing, including automatically generated identifiers, which are transferred into MISO by trained laboratory technicians (please refer to the TM. Sample Accessioning Procedure SOP).
Run Scanner (1.12.0+)
Run Scanner is a Java application which monitors sequencing run status http://runscanner.gsi.oicr.on.ca internal only) and is used to populate and update runs in the laboratory information management system (LIMS) – MISO, including marking them as complete.
Shesmu (1.4.2+)
Analysis is automated through decision-making software developed in-house called Shesmu (https://shesmu.gsi.oicr.on.ca/- internal network access only). Shesmu acts as an intermediary between several systems: MISO, a database of analysis provenance, and a workflow scheduler. Shesmu interfaces with MISO to retrieve sample metadata, and scans the provenance system for a list of which files have been produced and then uses decision-action blocks called “Olives” to decide what “actions” should be run. Actions can be launching analysis workflows, filing tickets in JIRA, generating reports, updating QC data, notifying operators about invalid data, requesting the laboratory technicians enter missing required data, and informing the lab of the current analysis progress. All production tasks pertaining to the monitoring and configuration of the informatics pipeline is performed via version-controlled Olives.
Vidarr (2.0.3)
Vidarr is an analysis provenance tracking server. It schedules workflows using a workflow engine like Cromwell workflow execution engine, collects the output from these workflows, and stores metadata about files and connections to Pinery LIMS information. Its primary components include a web service to track analysis, a command line interface for testing and development, and a base workflow engine (Cromwell), as well as tools for generating workflow definitions.
Workflows are written in the WDL language and contain all the commands for running bioinformatics software (including fastq generation, alignment, variant calling, annotation and generation of QC metrics; see Fig. 3 and Fig. 4 for flowchart of WGS and RNA bioinformatics workflows, respectively. See next section for details of the software components within WDLworkflows). Workflow runs and all associated files are tracked and recorded in Vidarr. This information is exposed as analysis provenance and used by the Provenance Client and Shesmu for automation.
Whizbam
Whizbam (https://whizbam.oicr.on.ca/) is an IGV.js server that can show segments of OICR BAM files in a web browser.
Other Software
These software applications are not developed by OICR Genomics but are integral to our process.
Grafana (6.7.0+)
Grafana is a graph-based monitoring tool used by Genomics to show trends in performance over time. It is not directly used in analysis.
Integrative Genomics Viewer (IGV)
IGV is a desktop application for examining genomic data, especially alignments, tracks, and other genomic region associated data.
JIRA (8.7.1+)
JIRA is a ticketing system used by Genomics to alert on issues that require human intervention. It is not directly used in analysis. Its use is further described in QM. LIMS Issue Management Plan.
OICR Univa Cluster
OICR’s high throughput computing cluster uses Univa. Software packages are installed using Modulator.
Change Log
Github commit log