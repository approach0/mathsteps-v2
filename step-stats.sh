if [ "$1" == "-h" ]; then
cat << USAGE
Usage: 统计生成训练集中的步骤数据
Examples:
$0 /path/to/corpus
USAGE
exit
fi

[ $# -ne 1 ] && echo 'bad arg.' && exit

path="$1"
total_num_files=$(find $path -name '*.txt' | wc -l)
total_num_lines=$(find $path -name '*.txt' | xargs wc -l | tail -1 | awk '{print $1}')
total_num_steps=$(bc <<< "${total_num_lines} - ${total_num_files}")
avg_num_steps=$(bc <<< "scale=3; ${total_num_steps} / ${total_num_files}")

echo "num_files: ${total_num_files}, num_lines: ${total_num_lines}"
echo "total steps: ${total_num_steps}"
echo "avg steps: ${avg_num_steps}"
