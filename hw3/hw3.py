import argparse
import logging
import os
import requests
import csv
import pandas as pd
import zipfile
import shutil
from datetime import datetime
from collections import defaultdict


TITLE_MAP = {
    'Mrs': 'missis',
    'Ms': 'miss',
    'Mr': 'mister',
    'Madame': 'mademoiselle'
}


def setup_logger(log_level):
    logging.basicConfig(
        filename='script.log',
        level=getattr(logging, log_level.upper(), 'INFO'),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def download_data():
    url = 'https://randomuser.me/api/?results=5000'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    logging.info('Data downloaded successfully.')
    return data['results']


def flatten_data(data):
    flat_data = []
    for i, user in enumerate(data):
        flat = {
            'global_index': i + 1,
            'gender': user['gender'],
            'title': TITLE_MAP.get(user['name']['title'], user['name']['title']),
            'first': user['name']['first'],
            'last': user['name']['last'],
            'country': user['location']['country'],
            'timezone_offset': user['location']['timezone']['offset'],
            'dob_date': user['dob']['date'],
            'dob_age': user['dob']['age'],
            'registered_date': user['registered']['date'],
            'id_name': user['id']['name'],
        }

        # Поточний час на основі timezone (грубо, без урахування DST)
        try:
            offset_hours = int(user['location']['timezone']['offset'].split(':')[0])
            current_time = datetime.utcnow() + pd.Timedelta(hours=offset_hours)
            flat['current_time'] = current_time.strftime('%H:%M:%S')
        except Exception:
            flat['current_time'] = ''

        flat_data.append(flat)
    logging.info('Data flattened.')
    return pd.DataFrame(flat_data)


def apply_filters(df, gender=None, rows=None):
    if gender:
        df = df[df['gender'].str.lower() == gender.lower()]
        logging.info(f"Filtered by gender: {gender}")
    if rows:
        df = df.head(int(rows))
        logging.info(f"Filtered by number of rows: {rows}")
    return df


def format_dates(df):
    df['dob_date'] = pd.to_datetime(df['dob_date']).dt.strftime('%m/%d/%Y')
    df['registered_date'] = pd.to_datetime(df['registered_date']).dt.strftime('%m-%d-%Y, %H:%M:%S')
    return df


def group_and_save(df, dest_folder):
    grouped = defaultdict(lambda: defaultdict(list))

    for _, row in df.iterrows():
        year = int(row['dob_date'].split('/')[-1])
        if year < 1960:
            continue
        decade = f"{(year // 10) * 10}-th"
        country = row['country']
        grouped[decade][country].append(row)

    for decade, countries in grouped.items():
        decade_path = os.path.join(dest_folder, decade)
        os.makedirs(decade_path, exist_ok=True)
        for country, rows in countries.items():
            country_path = os.path.join(decade_path, country)
            os.makedirs(country_path, exist_ok=True)
            df_country = pd.DataFrame(rows)
            if df_country.empty:
                continue
            max_age = df_country['dob_age'].max()
            df_country['registered_year'] = pd.to_datetime(df_country['registered_date'], errors='coerce').dt.year
            avg_reg = int(datetime.now().year - df_country['registered_year'].mean())
            popular_id = df_country['id_name'].mode().iloc[0] if not df_country['id_name'].mode().empty else 'unknown'
            filename = f"max_age_{max_age}_avg_registered_{avg_reg}_popular_id_{popular_id}.csv"
            file_path = os.path.join(country_path, filename)
            df_country.drop(columns=['registered_year'], inplace=True)
            df_country.to_csv(file_path, index=False)
            logging.info(f"Saved file: {file_path}")


def log_folder_structure(path, prefix=''):
    for item in sorted(os.listdir(path)):
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            logging.info(f"{prefix}[DIR] {item}")
            log_folder_structure(full_path, prefix + '\t')
        else:
            logging.info(f"{prefix}[FILE] {item}")


def archive_folder(folder):
    shutil.make_archive(folder, 'zip', folder)
    logging.info(f"Archived folder: {folder}.zip")


def main():
    parser = argparse.ArgumentParser(description='Process random users.')
    parser.add_argument('--destination', required=True, help='Destination folder')
    parser.add_argument('--filename', default='output', help='Base filename')
    parser.add_argument('--gender', help='Filter by gender')
    parser.add_argument('--rows', type=int, help='Limit number of rows')
    parser.add_argument('log_level', nargs='?', default='INFO', help='Logging level')
    args = parser.parse_args()

    setup_logger(args.log_level)

    os.makedirs(args.destination, exist_ok=True)
    os.chdir(args.destination)

    raw_data = download_data()
    df = flatten_data(raw_data)

    csv_raw = f"{args.filename}.csv"
    df.to_csv(csv_raw, index=False)
    logging.info(f"Initial data saved: {csv_raw}")

    df = apply_filters(df, args.gender, args.rows)
    df = format_dates(df)

    group_and_save(df, os.getcwd())
    log_folder_structure(os.getcwd())
    archive_folder(os.getcwd())


if __name__ == '__main__':
    main()
