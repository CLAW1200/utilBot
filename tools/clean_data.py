# Open data.csv and remove remove any lines where the first column has duplicate entries up to the hour
# use datetime strftime("%Y-%m-%d %H")

# Example of duplicate entries in data.csv
# 2023-12-21 18:00:42,4261,215,929
# 2023-12-21 19:00:43,4269,215,930
# 2023-12-21 19:00:43,4269,215,930
# 2023-12-21 19:00:43,4269,215,930
# 2023-12-21 19:00:43,4269,215,930
# 2023-12-21 20:00:44,4274,215,930
# 2023-12-21 20:00:44,4274,215,930
# 2023-12-21 20:00:44,4274,215,930
# 2023-12-21 20:00:44,4274,215,930
# 2023-12-21 21:00:44,4298,216,933
# 2023-12-21 21:00:44,4298,216,933
# 2023-12-21 21:00:44,4298,216,933
# 2023-12-21 21:00:44,4298,216,933


import csv
import datetime

def remove_duplicates(filename):
    seen_hours = set()
    output_rows = []

    with open(filename, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip the header row
        for row in reader:
            timestamp = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
            hour = timestamp.strftime("%Y-%m-%d %H")
            if hour not in seen_hours:
                output_rows.append(row)
                seen_hours.add(hour)

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(output_rows)



# Time,User Count,Server Count,Total Command Count
# 2024-01-02 17:00:18,22,2,53,
# 2024-01-02 18:00:09,22,2,62,
# 2024-01-02 18:00:55,22,2,62,
# 2024-01-02 19:00:36,22,2,70,
# 2024-01-02 21:00:11,22,2,80,
# 2024-01-03 09:00:19,22,2,85,
# 2024-01-03 11:00:04,22,2,87,
# 2024-01-04 20:00:46,21,2,106,
# 2024-01-04 21:00:56,21,2,111,



def add_col_to_csv(filename):
    command_count_index = 3
    rows = []

    with open(filename, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)

    for i in range(1, len(rows)):
        try:
            current_command_count = int(rows[i][command_count_index])
        except:
            continue
        try:
            previous_command_count = int(rows[i-1][command_count_index])
        except:
            continue
        command_difference = current_command_count - previous_command_count
        rows[i].append(command_difference)

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

if __name__ == '__main__':
    add_col_to_csv('data.csv')