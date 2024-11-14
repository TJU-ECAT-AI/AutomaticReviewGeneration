for i in 10.*
do 
  cd $i
  echo $i
  echo
  python3 ../py/GetAllResponse.py >> ../KnowledgeExtraction.log 2>&1
  python3 ../py/AnswerIntegration.py >> ../KnowledgeExtraction.log 2>&1
  python3 ../py/LinkAnswer.py >> ../KnowledgeExtraction.log 2>&1
  python3 ../py/SplitIntoFolders.py >> ../KnowledgeExtraction.log 2>&1
  cd Answer
  ln -s PART0/1 .
  cd ..
  echo
  cd ..
done


