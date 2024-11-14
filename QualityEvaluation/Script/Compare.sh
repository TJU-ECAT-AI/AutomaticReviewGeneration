for i in 10.*
do 
  cd $i
  echo $i
  echo
  cd Answer/Paragraph
  ln -s ../../../../TopicExtract/RawFromPDF/*/"$i".txt Paragraph1_9.txt
  ln -s ../../DirectGeneration/DirectGeneration1.txt Paragraph1_10.txt
  cd ../..
  python3 ../py/CompareTwoReviewArticles.py >> ../Compare.log 2>&1
  echo
  cd ..
done

