import requests
import os
import stat
import shutil
import git
import pyarrow.parquet as pq
import pandas as pd

def on_rm_error(func, path, exc_info):
    """
    Error handler for shutil.rmtree.

    If the error is due to an access issue, it attempts to fix the permissions and retries.
    Otherwise, it re-raises the error.
    """
    if not os.access(path, os.W_OK):
        # Attempt to fix the permissions and retry
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def import_data():
    working_dir = os.getcwd()

    #aggregate data
    repo_url = 'https://github.com/MoH-Malaysia/data-darah-public.git'
    folder_name = 'data_aggregate'
    clone_dir = os.path.join(working_dir,folder_name)
    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir, onerror=on_rm_error)

    git.Repo.clone_from(repo_url, clone_dir)

    #granular data
    gran_url = 'https://dub.sh/ds-data-granular'
    download_folder = os.path.join(working_dir, 'data_granular')
    filename = 'gran_data.parquet'
    file_path = os.path.join(download_folder, filename)
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    response = requests.get(gran_url)
    if response.status_code == 200:
        # Write the file contents to the file
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"File downloaded successfully and saved as {file_path}")
    else:
        print(f"Failed to retrieve data. HTTP Status Code: {response.status_code}")
        quit()
     #read file as pandas
    facility_df = pd.read_csv('.\data_aggregate\donations_facility.csv')
    gran_df = pd.read_parquet(file_path)

    return (facility_df, gran_df)
    