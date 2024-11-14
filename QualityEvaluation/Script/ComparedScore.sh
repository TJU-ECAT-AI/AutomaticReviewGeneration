for i in 10.*
do 
  cd $i
  echo $i
  echo
  cd Answer/Paragraph/CompareParagraph/
  python3 ../../../../py/ComparedScore.py >> ComparedScore.log 2>&1
  cd ../../..
  echo
  cd ..
done

mkdir ComparedResult
cd ComparedResult
for i in ../10.*; do
  for file in $i/Answer/Paragraph/CompareParagraph/*.csv; do
    ln -s "$file" "$(basename $i)_$(basename $file)"
  done
done
