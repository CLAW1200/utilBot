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

if __name__ == '__main__':
    remove_duplicates('data.csv')