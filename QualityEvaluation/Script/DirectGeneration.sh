for i in 10.*
do 
  cd $i
  echo $i
  echo
  python3 ../py/DirectGeneration.py >> ../DirectGeneration.log 2>&1
  echo
  cd ..
done


