#!/bin/bash

# 遍历 Papers 目录下的所有子目录
for dir in Papers/*/; do
    # 获取子目录名称
    dirname=$(basename "$dir")
    
    # 遍历子目录中的数字文件夹
    for i in {0..14}; do
        if [ -d "${dir}${i}" ]; then
            # 创建目标目录
            mkdir -p "${dirname}_${i}/RawFromPDF"
            
            # 复制文件
            cp "${dir}${i}"/*.txt "${dirname}_${i}/RawFromPDF/" 2>/dev/null
        fi
    done
done
python3 py/WriteTopic.py
for i in 10.*;do cd $i;python3 ../py/XMLFormattedPrompt.py;mkdir Prompt;mv Prompt* Prompt;cd ..;done

echo "文件复制完成。"
