import argparse
import csv
import logging
import os
import shutil
import zipfile
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from pathlib import Path
import requests
import pandas as pd

# пр. еом. D:\folder --filename output --gender male --rows 100

title_map = {
    'Mrs': 'missis',
    'Ms': 'miss',
    'Mr': 'mister',
    'Madame': 'mademoiselle'
}

parser = argparse.ArgumentParser(description="Prepare user data for analysis.")
parser.add_argument('destination_folder', type=str, help='Path to output folder')
parser.add_argument('--filename', type=str, default='output', help='Output file name')
parser.add_argument('--gender', type=str, choices=['male', 'female'], help='Filter by gender')
parser.add_argument('--rows', type=int, help='Number of rows to keep')
parser.add_argument('log_level', nargs='?', default='INFO', help='Logging level')
args = parser.parse_args()

logging.basicConfig(
    filename='processing.log',
    level=getattr(logging, args.log_level.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Script started")

output_path = Path(args.destination_folder)
output_path.mkdir(parents=True, exist_ok=True)
os.chdir(output_path)

download_url = 'https://randomuser.me/api/?results=5000&format=csv'
logging.info("Downloading data from RandomUser API")
response = requests.get(download_url)
csv_path = output_path / f"{args.filename}.csv"
with open(csv_path, 'w', encoding='utf-8') as f:
    f.write(response.text)
logging.info(f"Downloaded and saved CSV to {csv_path}")

df = pd.read_csv(csv_path)
if args.gender:
    df = df[df['gender'] == args.gender]
    logging.info(f"Filtered data by gender: {args.gender}, remaining rows: {len(df)}")
if args.rows:
    df = df.head(args.rows)
    logging.info(f"Filtered data to {args.rows} rows")

df.reset_index(drop=True, inplace=True)
df['global_index'] = df.index

now_utc = datetime.utcnow()
def get_current_time(offset_str):
    try:
        offset = timedelta(hours=int(offset_str[:3]), minutes=int(offset_str[0] + offset_str[4:]))
        local_time = now_utc + offset
        return local_time.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ''

df['current_time'] = df['location.timezone.offset'].apply(get_current_time)
df['name.title'] = df['name.title'].apply(lambda x: title_map.get(x, x))
df['dob.date'] = pd.to_datetime(df['dob.date']).dt.strftime('%m/%d/%Y')
df['registered.date'] = pd.to_datetime(df['registered.date']).dt.strftime('%m-%d-%Y, %H:%M:%S')

df['birth_year'] = pd.to_datetime(df['dob.date']).dt.year
df = df[df['birth_year'] >= 1960]
logging.info(f"Removed users born before 1960. Remaining rows: {len(df)}")

structure = defaultdict(lambda: defaultdict(list))
for _, row in df.iterrows():
    decade = f"{int(row['birth_year'] // 10) * 10}-th"
    country = row['location.country']
    structure[decade][country].append(row)

for decade, countries in structure.items():
    decade_folder = output_path / decade
    decade_folder.mkdir(exist_ok=True)
    for country, rows in countries.items():
        country_folder = decade_folder / country
        country_folder.mkdir(exist_ok=True)
        group_df = pd.DataFrame(rows)
        max_age = group_df['dob.age'].max()
        avg_registered = round(group_df['registered.age'].mean())
        popular_id = Counter(group_df['id.name']).most_common(1)[0][0]
        filename = f"max_age_{max_age}_avg_registered_{avg_registered}_popular_id_{popular_id}.csv"
        file_path = country_folder / filename
        group_df.to_csv(file_path, index=False)
        logging.info(f"Saved file: {file_path}")

def log_folder_structure(path: Path, level=0):
    for item in sorted(path.iterdir()):
        prefix = '📄' if item.is_file() else '📁'
        indent = "\t" * level
        logging.info(f"{indent}{prefix} {item.name}")
        if item.is_dir():
            log_folder_structure(item, level + 1)

log_folder_structure(output_path)

zip_path = output_path.with_suffix('.zip')
shutil.make_archive(str(output_path), 'zip', root_dir=output_path)
logging.info(f"Archived folder to: {zip_path}")
logging.info("Script finished")
