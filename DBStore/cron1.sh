# This file is used for putting the job dbstore.py in crontab

file_path=$PWD/"dbstore.py"   #dbstore.py: storing info in DB
py=`which python`             #python version
command="$py $file_path"      #command for the job
crontab -l > mycron           
echo "*/1 * * * * $command" >> mycron     #interval 1 minute
crontab mycron                            #staring the job
rm mycron                                   



