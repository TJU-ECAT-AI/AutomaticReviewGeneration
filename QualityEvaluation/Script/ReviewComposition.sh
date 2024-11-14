for i in 10.*
do 
  cd $i
  echo $i
  echo
  python3 ../py/GenerateParagraphOfReview.py >> ../ReviewComposition.log 2>&1
  python3 ../py/GenerateRatingsForReviewParagraphs.py >> ../ReviewComposition.log 2>&1
  python3 ../py/ExtractSectionsWithTags.py >> ../ReviewComposition.log 2>&1
  echo
  cd ..
done


