#!/bin/bash
STUDY_ID=$1

# echo "Deleting files associated with studyId=$STUDY_ID"
echo "delete from file where id in (
	select file.id from study 
		left join donor on study.id=donor.study_id 
		left join specimen on donor.id=specimen.donor_id 
		left join sample on specimen.id=sample.specimen_id 
		left join sampleset on sampleset.sample_id=sample.id 
		left join analysis on sampleset.analysis_id=analysis.id 
		left join file on file.analysis_id=analysis.id 
		where study.id='$STUDY_ID');"

echo ""
echo "delete from sampleset where sample_id in (
	select sampleset.sample_id from study 
		left join donor on study.id=donor.study_id 
		left join specimen on donor.id=specimen.donor_id 
		left join sample on specimen.id=sample.specimen_id 
		left join sampleset on sampleset.sample_id=sample.id 
		where study.id='$STUDY_ID');"

#echo "delete from analysis_data where id in (
    #select analysis.analysis_data_id from analysis 
		#left join analysis_data on analysis_data.id=analysis.analysis_data_id 
		#where study_id='$STUDY_ID');"

echo ""
echo "delete from analysis where study_id='$STUDY_ID'";

echo ""
echo "delete from sample where id in (
	select sample.id from study 
		left join donor on study.id=donor.study_id 
		left join specimen on donor.id=specimen.donor_id 
		left join sample on specimen.id=sample.specimen_id 
		where study.id='$STUDY_ID');"

echo ""
echo "delete from specimen where id in (
	select specimen.id from study 
		left join donor on study.id=donor.study_id 
		left join specimen on donor.id=specimen.donor_id 
		where study.id='$STUDY_ID');"


echo ""
echo "delete from donor where id in (
	select donor.id from study 
		left join donor on study.id=donor.study_id 
		where study.id='$STUDY_ID');"

echo ""
echo "delete from study where id='$STUDY_ID'"
