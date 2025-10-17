# Assays

Source: https://oicr-gsi.readthedocs.io/en/latest/informatics-pipelines/assays.html

Assays
View page source
Assays
Whole Genome and Transcriptome (WGTS) version 6.0
Targeted Sequencing (TAR) version 6.0
Shallow Whole Genome (sWGS) version 3.0
Plasma Whole Genome (pWGS) version 3.0
Reference Files
Reference
Version
Source
Internal
Human Genome Reference
hg38-p12
UCSC
Modulator
Whole-genome interval file
hg38-p12 all intervals
Interval-files
Exome interval file for callability
Agilent SureSelect Exome V6
UCSC
Interval-files
TS REVOLVE revolve-panel
Paper
Excel file
Interval-files
Whole Genome and Transcriptome (WGTS) version 6.0
Whole Genome
Fig. 3 Whole Genome Sequencing Analysis Pipeline
The whole genome pipeline commences once the bcl2fastq workflow is completed and FASTQ files are available (not shown).
FASTQ files are quality controlled using FastQC. FastQC produces quality control metrics related to reads (e.g. total numbers of reads).
FASTQ files are aligned with BwaMem2 to generate an unprocessed lane-level BAM file.
Cases are quality controlled with the - bamQCworkflow generating a JSON file of lane-level alignment QC metrics for review. The quality control metrics include the insert size distribution, amount of duplication, mapping percentage, and other WG ‘Single Lane’ metrics described in QM. Quality Control and Calibration Procedures. Genomic fingerprints are generated from lane-level alignments and made available to sample authentication procedures.
Cases are quality controlled again with bamQC running on the merged set of all lane-level alignments generating a JSON file of call-ready alignment QC metrics for review. In addition to the lane-level QC metrics this includes an assessment of the per-sample depth of coverage (QM. Quality Control and Calibration Procedures).
All lane-level BAM files are collected and processed via BamMergePreProcessing, which merges and sorts lane-level BAMs, as well as performing duplicate marking, and base quality score recalibration to generate a call-ready sample-level BAM..
These normal and tumour BAM files are used as input for the variant calling workflows.
MuTect2 generates SNV and INDEL mutation calls in vcf format, which are annotated by VariantEffectPredictor, generating a MAF file of annotated calls.
GRIDSS and Delly generate somatic structural alterations in VCF format. The Delly vcf is post-processed by MAVIS to generate calls in TSV format, in addition to graphical representations of the structural event in SVG format.
The GRIDSS vcf is post-processed by Purple and used for evidence to support copy number calls, loss of heterozygosity status, and estimate tumour purity.
msisensor calls the proportion of microsatellite sites with evidence of variants between T-N to produce a microsatellite score recorded in a .TXT file.
HRDetect calls the homologous recombination deficiency (HRD) status using the Mutect2 vcf file, and the GRIDSS vcf file as input. The output file is a json file containing the HRD results.
T1K reports germline HLA typing alleles by estimating allele abundances from input read alignments. The output is a TSV file that includes the identified HLA alleles, their abundance, quality, and any secondary alleles.
All alteration files are provided to Djerba to generate a provisional clinical report for review by genome interpreters.
WGS Workflows and Software
More information about the analysis pipelines is available in the ‘Procedure’ section below. Workflow parameterization is automated through the linked Shesmu configuration. This repository is restricted to authorized individuals.
Human Genome Reference: hg38-p12
Source: UCSC
Local fasta: Modulator
Table 1 Whole Genome Sequencing Software
Workflow
Version
Parameterization
Reference Data
Bioinformatics Software
bamMergePreprocessing
2.1.1
vidarr-u20-bmpp-bysample.shesmu vidarr-u20-bmpp.shesmu
python/3.7 python/2.7 gatk/4.1.6.0 gatk/3.6-0 samtools/1.9
bamqc
5.1.3
vidarr-u20-bamqc-call-ready.shesmu vidarr-u20-bamqc-lane-level.shesmu
bam-qc-metrics/0.2.5 python/3.6 mosdepth/0.2.9 gatk/4.1.6.0 picard/2.21.2 samtools/1.14 samtools/1.9
bcl2barcode
1.0.2
vidarr-u20-bcl2barcode.shesmu
bcl2fastq/2.20.0.422 htslib/1.9
bcl2fastq
3.1.3
vidarr-u20-bcl2fastq.shesmu
barcodex-rs/0.1.2 bcl2fastq-jail/3.1.2b bcl2fastq/2.20.0.422
bwamem2
1.0.1
vidarr-u20-bwamem2.shesmu
hg19-bwamem2-index/2.2.1 hg38-bwamem2-index-with-alt/2.2.1
barcodex-rs/0.1.2 python/3.7 slicer/0.3.0 rust/1.45.1 cutadapt/1.8.3 bwa-mem2/2.2.1 samtools/1.9
callability
1.3.0
vidarr-u20-metrics-WGS-callability-bysample.shesmu
python/3.7 mosdepth/0.2.9 bedtools/2.27
crosscheckFingerprintsCollector
1.1.0
vidarr-u20-crosscheckFingerprintsCollector\_fastq\_exceptions.shesmu vidarr-u20-crosscheckFingerprintsCollector\_bam.shesmu vidarr-u20-crosscheckFingerprintsCollector\_fastq.shesmu
hg38-star-index100/2.7.3a hg19-bwa-index/0.7.17 hg19-star-index100/2.7.3a hg38-bwa-index-with-alt/0.7.17
samtools/1.15 crosscheckfingerprints-haplotype-map/20230324 tabix/0.2.6 seqtk/1.3 star/2.7.3a bwa/0.7.17 gatk/4.1.6.0 samtools/1.14 gatk/4.2.0.0 samtools/1.9
delly
2.6.1
vidarr-u20-delly\_matched-bysample.shesmu
hg38-delly/1.0 hg19-delly/1.0
vcftools/0.1.16 tabix/0.2.6 java/8 bcftools/1.9 picard/2.19.2 delly/0.9.1
dnaSeqQC
1.1.0
vidarr-u20-dnaseqqc.shesmu
hg19-bwa-index/0.7.12 hg38-bwa-index/0.7.12 mm10-bwa-index/0.7.12
bwa/0.7.12 mosdepth/0.2.9 bam-qc-metrics/0.2.5 slicer/0.3.0 python/3.6 cutadapt/1.8.3 picard/2.21.2 samtools/1.9
fastqc
3.2.0
vidarr-u20-fastqc.shesmu
java/11 fastqc/0.11.9 perl/5.28
gridss
1.3.1
vidarr-u20-gridss-bysample.shesmu
hg38-gridss-index/1.0 hmftools-data/53138
gatk/4.1.6.0 samtools/1.14 hmftools/1.1 gridss/2.13.2m
hrDetect
1.6.0
vidarr-u20-hrDetect.shesmu
hg38-dac-exclusion/1.0 sigtools-data/1.0
hrdetect-rscript/1.5.8 bcftools/1.9 tabix/1.9 sigtools/2.4.1
mavis
3.3.3
vidarr-u20-mavis\_clinical.shesmu vidarr-u20-mavis\_non\_clinical.shesmu
hg38v110-mavis/2.2.6
bcftools/1.9 mavis-config/1.2 mavis/2.2.6
msisensor
1.2.0
vidarr-u20-msisensor.shesmu
msisensorpro/1.2.0
mutect2
1.0.9
vidarr-u20-mutect2\_tumor\_only.shesmu vidarr-u20-mutect2\_normal\_only.shesmu vidarr-u20-mutect2\_matched-bysample.shesmu
hg38-gatk-gnomad/2.0
samtools/1.9
purple
1.1.3
vidarr-u20-purple.shesmu
hg38-gridss-index/1.0 hmftools-data/53138 hg38-dac-exclusion/1.0
python/3.10.6 bcftools/1.9 gatk/4.1.6.0 hmftools/1.1
t1k
1.2.0
vidarr-u20-t1k.shesmu
t1k/1.0.2
variantEffectPredictor
2.5.0
vidarr-u20-variantEffectPredictor\_matched-bysample.shesmu vidarr-u20-variantEffectPredictor\_tumor\_only.shesmu
vep-hg19-cache/105 vep-mm39-cache/105 vep-hg38-cache/105
bedtools/2.27 tabix/0.2.6 vep/105.0 bcftools/1.9 vcf2maf/1.6.21b gatk/4.1.7.0
wgsmetrics
1.1.0
vidarr-u20-metrics-WGS.shesmu
picard/2.21.2
Whole Transcriptome
Fig. 4 Whole Transcriptome Sequencing Analysis Pipeline
As with the WGS informatics pipeline, the whole transcriptome pipeline commences once FASTQ files are generated from bcl2fastq.
FASTQ files are aligned with the STAR workflow, generating genome-aligned and transcriptome-aligned BAM files. STAR also outputs a TSV file of chimeric junctions which is used as input for the STAR-Fusion workflow.
The FASTQ files are also provided to RNASeqQc which generates a JSON file of QC metrics for plotting via Dashi. The quality control metrics include the WT ‘Single Lane’ metrics described in QM. Quality Control and Calibration Procedures. Genomic fingerprints are generated from lane-level alignments and made available to sample authentication procedures.
The transcriptome-aligned BAM file is provided as input to RSEM, generating FPKM values and normalized expression counts in tabular format.
RNA fusion calls are generated from STAR-Fusion and Aribba. Both are used as input to to MAVIS for validation and annotation.
All alteration files are provided to Djerba to generate a provisional clinical report for review by genome interpreters.
TS Workflows and Software
More information about the analysis pipelines is available in the ‘Procedure’ section below. Workflow parameterization is automated through the linked Shesmu configuration. This repository is restricted to authorized individuals.
Table 2 Whole Transcriptome Sequencing Software
Workflow
Version
Parameterization
Reference Data
Bioinformatics Software
arriba
2.4.0
vidarr-u20-arriba.shesmu
gencode/31 rarriba/0.1 arriba/2.4.0 samtools/1.16.1
bcl2barcode
1.0.2
vidarr-u20-bcl2barcode.shesmu
bcl2fastq/2.20.0.422 htslib/1.9
bcl2fastq
3.1.3
vidarr-u20-bcl2fastq.shesmu
barcodex-rs/0.1.2 bcl2fastq-jail/3.1.2b bcl2fastq/2.20.0.422
crosscheckFingerprintsCollector
1.1.0
vidarr-u20-crosscheckFingerprintsCollector\_fastq\_exceptions.shesmu vidarr-u20-crosscheckFingerprintsCollector\_bam.shesmu vidarr-u20-crosscheckFingerprintsCollector\_fastq.shesmu
hg38-star-index100/2.7.3a hg19-bwa-index/0.7.17 hg19-star-index100/2.7.3a hg38-bwa-index-with-alt/0.7.17
samtools/1.15 crosscheckfingerprints-haplotype-map/20230324 tabix/0.2.6 seqtk/1.3 star/2.7.3a bwa/0.7.17 gatk/4.1.6.0 samtools/1.14 gatk/4.2.0.0 samtools/1.9
fastqc
3.2.0
vidarr-u20-fastqc.shesmu
java/11 fastqc/0.11.9 perl/5.28
mavis
3.3.3
vidarr-u20-mavis\_clinical.shesmu vidarr-u20-mavis\_non\_clinical.shesmu
hg38v110-mavis/2.2.6
bcftools/1.9 mavis-config/1.2 mavis/2.2.6
rnaseqqc
1.3.0
vidarr-u20-rnaseqqc-lane\_level.shesmu vidarr-u20-rnaseqqc-call\_ready.shesmu
hg38-star-index100/2.7.3a hg19-star-index100/2.6.0c
production-tools-python/2 bwa/0.7.17 star/2.7.3a picard/2.19.2 star/2.6.0c bam-qc-metrics/0.2.5 rnaseqqc-ribosome-grch38-bwa-index/1.0.0 jq/1.6 picard/2.21.2 samtools/1.9
rsem
1.0.1
vidarr-u20-rsem.shesmu
hg38-rsem-index/1.3.0 hg19-rsem-index/1.3.3
rsem/1.3.3
star
2.3.0
vidarr-u20-star\_lane\_level.shesmu vidarr-u20-star\_call\_ready.shesmu
hg38-star-index100/2.7.10b hg19-star-index100/2.7.10b
picard/2.19.2
starfusion
2.0.2
vidarr-u20-starfusion.shesmu
star-fusion-genome/1.8.1-hg38
star-fusion/1.8.1
Targeted Sequencing (TAR) version 6.0
Fig. 5 Targeted Sequencing Analysis Pipeline
As with the WGTS informatics pipeline, the targeted sequencing pipeline commences once FASTQ files are generated from bcl2fastq.
FASTQ files are aligned with BwaMem to generate an unprocessed lane-level BAM file.
Cases are quality controlled with the bamQC workflow generating a JSON file of lane-level alignment QC metrics for review. The quality control metrics include the insert size distribution, amount of duplication, mapping percentage, and other TAR ‘Single Lane’ metrics described in QM. Quality Control and Calibration Procedures. Genomic fingerprints are generated from lane-level alignments and made available to sample authentication procedures.
All lane-level BAM files are collected and processed via BamMergePreProcessing, which merges and sorts lane-level BAMs, as well as performing duplicate marking, and base recalibration to generate a call-ready sample-level BAM.
The FASTQ files are also processed with ConsensusCruncherWorkflow to generate UMI-tagged and consensus-collapsed bam files. The ConsensusCruncherWorkflow uses MuTect2 followed by Variant Effect Predictor to generate raw call files, and HSMetrics to generate collapsed coverage metrics. For variant calling, the duplex consensus sequences and single-stand consensus sequence with singleton corrected bam files are used to generate raw calls, which are then annotated with the variant allele frequency from the all-unique bam file.
All alteration files are provided to Djerba to generate a provisional clinical report for review by genome interpreters.
TAR Workflows and Software
Human Genome Reference: hg38-p12
Source: UCSC
Internal fasta: Modulator
REVOLVE panel: Paper
Internal link: Interval-files
Table 3 Targeted Sequencing Software
Workflow
Version
Parameterization
Reference Data
Bioinformatics Software
bamMergePreprocessing
2.1.1
vidarr-u20-bmpp-bysample.shesmu vidarr-u20-bmpp.shesmu
python/3.7 python/2.7 gatk/4.1.6.0 gatk/3.6-0 samtools/1.9
bamqc
5.1.3
vidarr-u20-bamqc-call-ready.shesmu vidarr-u20-bamqc-lane-level.shesmu
bam-qc-metrics/0.2.5 python/3.6 mosdepth/0.2.9 gatk/4.1.6.0 picard/2.21.2 samtools/1.14 samtools/1.9
bcl2fastq
3.1.3
vidarr-u20-bcl2fastq.shesmu
barcodex-rs/0.1.2 bcl2fastq-jail/3.1.2b bcl2fastq/2.20.0.422
bwaMem
1.0.0
vidarr-u20-bwaMem.shesmu
:mm10-bwa-index/0.7.17 hg19-bwa-index/0.7.17 hg38-bwa-index-with-alt/0.7.17 hg19-bwa-index/0.7.12 hg38-bwa-index-with-alt/0.7.12
bwa/0.7.12 barcodex-rs/0.1.2 python/3.7 slicer/0.3.0 cutadapt/1.8.3 rust/1.45.1 bwa/0.7.17 samtools/1.9
consensusCruncher
1.4.0
vidarr-u20-consensusCruncher.shesmu
hg19-bwa-index/0.7.12 hg38-bwa-index-with-alt/0.7.12 data-hg19-consensus-cruncher/1.0 data-hg38-consensus-cruncher/1.0
tabix/0.2.6 bcftools/1.9 gatk/3.6-0 htslib/1.9 consensus-cruncher/5.0 tabix/1.9 samtools/1.9
crosscheckFingerprintsCollector
1.1.0
vidarr-u20-crosscheckFingerprintsCollector\_fastq\_exceptions.shesmu vidarr-u20-crosscheckFingerprintsCollector\_bam.shesmu vidarr-u20-crosscheckFingerprintsCollector\_fastq.shesmu
hg38-star-index100/2.7.3a hg19-bwa-index/0.7.17 hg19-star-index100/2.7.3a hg38-bwa-index-with-alt/0.7.17
samtools/1.15 crosscheckfingerprints-haplotype-map/20230324 tabix/0.2.6 seqtk/1.3 star/2.7.3a bwa/0.7.17 gatk/4.1.6.0 samtools/1.14 gatk/4.2.0.0 samtools/1.9
dnaSeqQC
1.1.0
vidarr-u20-dnaseqqc.shesmu
hg19-bwa-index/0.7.12 hg38-bwa-index/0.7.12 mm10-bwa-index/0.7.12
bwa/0.7.12 mosdepth/0.2.9 bam-qc-metrics/0.2.5 slicer/0.3.0 python/3.6 cutadapt/1.8.3 picard/2.21.2 samtools/1.9
fastqc
3.2.0
vidarr-u20-fastqc.shesmu
java/11 fastqc/0.11.9 perl/5.28
mutect2
1.0.9
vidarr-u20-mutect2\_tumor\_only.shesmu vidarr-u20-mutect2\_normal\_only.shesmu vidarr-u20-mutect2\_matched-bysample.shesmu
hg38-gatk-gnomad/2.0
samtools/1.9
variantEffectPredictor
2.5.0
vidarr-u20-variantEffectPredictor\_matched-bysample.shesmu vidarr-u20-variantEffectPredictor\_tumor\_only.shesmu
vep-hg19-cache/105 vep-mm39-cache/105 vep-hg38-cache/105
bedtools/2.27 tabix/0.2.6 vep/105.0 bcftools/1.9 vcf2maf/1.6.21b gatk/4.1.7.0
Shallow Whole Genome (sWGS) version 3.0
Fig. 6 Shallow Whole Genome Analysis Pipeline
The shallow whole genome pipeline commences once the bcl2fastq workflow is completed and FASTQ files are available.
FASTQ files are quality controlled using FastQC. FastQC produces quality control metrics related to reads (e.g. total numbers of reads)
FASTQ files are aligned with BwaMem2 to generate an unprocessed lane-level BAM file.
Data is quality controlled with the bamQC workflow generating a JSON file of alignment QC metrics for review. The quality control metrics include the insert size distribution, amount of duplication, mapping percentage, and other WG ‘Single Lane’ metrics described in QM. Quality Control and Calibration Procedures.
The BAM files are processed with ichorCNA to estimate tumour fractions in ultra-low pass whole genome sequencing (WGS) and prediction of large-scale copy number variation (CNV).
All alteration files are provided to Djerba to generate a provisional clinical report for review by genome interpreters.
sWGS Workflows and Software
Human Genome Reference: hg38-p12
Source: UCSC
Local fasta: Modulator
Table 4 Shallow Whole Genome Sequencing Software
Workflow
Version
Parameterization
Reference Data
Bioinformatics Software
bcl2fastq
3.1.3
vidarr-u20-bcl2fastq.shesmu
barcodex-rs/0.1.2 bcl2fastq-jail/3.1.2b bcl2fastq/2.20.0.422
bwamem2
1.0.1
vidarr-u20-bwamem2.shesmu
hg19-bwamem2-index/2.2.1 hg38-bwamem2-index-with-alt/2.2.1
barcodex-rs/0.1.2 python/3.7 slicer/0.3.0 rust/1.45.1 cutadapt/1.8.3 bwa-mem2/2.2.1 samtools/1.9
crosscheckFingerprintsCollector
1.1.0
vidarr-u20-crosscheckFingerprintsCollector\_fastq\_exceptions.shesmu vidarr-u20-crosscheckFingerprintsCollector\_bam.shesmu vidarr-u20-crosscheckFingerprintsCollector\_fastq.shesmu
hg38-star-index100/2.7.3a hg19-bwa-index/0.7.17 hg19-star-index100/2.7.3a hg38-bwa-index-with-alt/0.7.17
samtools/1.15 crosscheckfingerprints-haplotype-map/20230324 tabix/0.2.6 seqtk/1.3 star/2.7.3a bwa/0.7.17 gatk/4.1.6.0 samtools/1.14 gatk/4.2.0.0 samtools/1.9
dnaSeqQC
1.1.0
vidarr-u20-dnaseqqc.shesmu
hg19-bwa-index/0.7.12 hg38-bwa-index/0.7.12 mm10-bwa-index/0.7.12
bwa/0.7.12 mosdepth/0.2.9 bam-qc-metrics/0.2.5 slicer/0.3.0 python/3.6 cutadapt/1.8.3 picard/2.21.2 samtools/1.9
fastqc
3.2.0
vidarr-u20-fastqc.shesmu
java/11 fastqc/0.11.9 perl/5.28
ichorcna
1.2.0
vidarr-u20-ichorcna.shesmu
hg19-bwa-index/0.7.12 hg38-bwa-index-with-alt/0.7.12
python/3.6 hmmcopy-utils/0.1.1 samtools/1.14 bwa/0.7.12 pandas/1.4.2 bam-qc-metrics/0.2.5 mosdepth/0.2.9 ichorcna/0.2 picard/2.21.2 samtools/1.9
Plasma Whole Genome (pWGS) version 3.0
Fig. 7 Plasma Whole Genome Analysis Pipeline
The plasma whole genome pipeline commences once the bcl2fastq workflow is completed and FASTQ files are available (not shown).
FASTQ files are quality controlled using FastQC. FastQC produces quality control metrics related to reads (e.g. total numbers of reads).
FASTQ files are aligned with BwaMem2 to generate an unprocessed lane-level BAM file.
Cases are quality controlled with the bamQCworkflow generating a JSON file of alignment QC metrics for review. The quality control metrics include the insert size distribution, amount of duplication, mapping percentage, and other WG ‘Single Lane’ metrics described in QM. Quality Control and Calibration Procedures.
Cases are quality controlled again with bamQC running on the merged set of all lane-level alignments generating a JSON file of call-ready alignment QC metrics for review. In addition to the lane-level QC metrics this includes an assessment of the per-sample depth of coverage (QM. Quality Control and Calibration Procedures).
All lane-level BAM files are collected and processed via BamMergePreProcessing, which merges and sorts lane-level BAMs, as well as performing duplicate marking, and base quality score recalibration to generate a call-ready sample-level BAM.
The plasma whole genome BAM file and an existing whole genome sequencing vcf file from matched donor are used as input for the mrdetect workflow.
MRDetect detects SNVs from WGS VCF in plasma BAM
MRDetect detects SNVs from WGS VCF in healthy blood control (HBC) cohort
Metrics are computed on the confidence of minimal residual disease detection
All alteration files are provided to Djerba to generate a provisional clinical report for review by genome interpreters.
pWGS Workflows and Software
More information about the analysis pipelines is available in the ‘Procedure’ section below. Workflow parameterization is automated through the linked Shesmu configuration. This repository is restricted to authorized individuals.
Table 5 Plasma Whole Genome Sequencing Software
Workflow
Version
Parameterization
Reference Data
Bioinformatics Software
bamMergePreprocessing
2.1.1
vidarr-u20-bmpp-bysample.shesmu vidarr-u20-bmpp.shesmu
python/3.7 python/2.7 gatk/4.1.6.0 gatk/3.6-0 samtools/1.9
bamqc
5.1.3
vidarr-u20-bamqc-call-ready.shesmu vidarr-u20-bamqc-lane-level.shesmu
bam-qc-metrics/0.2.5 python/3.6 mosdepth/0.2.9 gatk/4.1.6.0 picard/2.21.2 samtools/1.14 samtools/1.9
bcl2barcode
1.0.2
vidarr-u20-bcl2barcode.shesmu
bcl2fastq/2.20.0.422 htslib/1.9
bcl2fastq
3.1.3
vidarr-u20-bcl2fastq.shesmu
barcodex-rs/0.1.2 bcl2fastq-jail/3.1.2b bcl2fastq/2.20.0.422
bwamem2
1.0.1
vidarr-u20-bwamem2.shesmu
hg19-bwamem2-index/2.2.1 hg38-bwamem2-index-with-alt/2.2.1
barcodex-rs/0.1.2 python/3.7 slicer/0.3.0 rust/1.45.1 cutadapt/1.8.3 bwa-mem2/2.2.1 samtools/1.9
callability
1.3.0
vidarr-u20-metrics-WGS-callability-bysample.shesmu
python/3.7 mosdepth/0.2.9 bedtools/2.27
crosscheckFingerprintsCollector
1.1.0
vidarr-u20-crosscheckFingerprintsCollector\_fastq\_exceptions.shesmu vidarr-u20-crosscheckFingerprintsCollector\_bam.shesmu vidarr-u20-crosscheckFingerprintsCollector\_fastq.shesmu
hg38-star-index100/2.7.3a hg19-bwa-index/0.7.17 hg19-star-index100/2.7.3a hg38-bwa-index-with-alt/0.7.17
samtools/1.15 crosscheckfingerprints-haplotype-map/20230324 tabix/0.2.6 seqtk/1.3 star/2.7.3a bwa/0.7.17 gatk/4.1.6.0 samtools/1.14 gatk/4.2.0.0 samtools/1.9
dnaSeqQC
1.1.0
vidarr-u20-dnaseqqc.shesmu
hg19-bwa-index/0.7.12 hg38-bwa-index/0.7.12 mm10-bwa-index/0.7.12
bwa/0.7.12 mosdepth/0.2.9 bam-qc-metrics/0.2.5 slicer/0.3.0 python/3.6 cutadapt/1.8.3 picard/2.21.2 samtools/1.9
fastqc
3.2.0
vidarr-u20-fastqc.shesmu
java/11 fastqc/0.11.9 perl/5.28
mrDetect
hg38-dac-exclusion/1.0
pwgs-hbc/2.0 pwgs-hbc/1.0 mrdetect/2.0.0 mrdetect/1.1.1 bcftools/1.9
wgsmetrics
1.1.0
vidarr-u20-metrics-WGS.shesmu
picard/2.21.2
Change Log
Github commit log