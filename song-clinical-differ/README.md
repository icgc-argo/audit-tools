# Song Clinical Differ

## Description
The purpose of this tool, is to audit whether all the donorIds, specimenIds and sampleIds in SONG are a subset of those in clinical. If there are ids in SONG that are NOT in clinical, the report will indicate missing ids.
This tool is particularily useful when the clinical service SONG pointed to was changed. This ensures data consistency. Before running this tool, ensure SONG service is not running, so there is no modification to the database while auditing.

## Requirements
- python >= 3.5 
- vitrualenv

## Initialize Env

```bash
virtualenv -p  python  test-venv
source test-venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python song-clinical-differ.py --jwt <jwt>  --song-url https://song.example.org --clinical-url https://clincal.example.org
```
