"""
SPDX-License-Identifier: Apache-2.0
Copyright : JP Morgan Chase & Co

Data Preparation for CyberBench Text Classification
"""
import os
import re
import shutil
import urllib
import pandas as pd
from markdown import markdown
from bs4 import BeautifulSoup
from mitreattack.stix20 import MitreAttackData
from utils import split_dataset, assign_instructions, drop_long_sequences

tc_folder = os.path.join('data', 'tc')
mitre_folder = os.path.join(tc_folder, 'mitre')
cve_folder = os.path.join(tc_folder, 'cve')
web_folder = os.path.join(tc_folder, 'web')
email_folder = os.path.join(tc_folder, 'email')
http_folder = os.path.join(tc_folder, 'http')

mitre_instructions = [
    "Determine the MITRE ATT&CK technique ID and name that best corresponds to the given procedure example.",
    "Identify the most suitable MITRE ATT&CK technique ID and name for the provided procedure example.",
    "Analyze the procedure example and provide the matching MITRE ATT&CK technique ID and name.",
    "From the procedure example, deduce the relevant MITRE ATT&CK technique ID and name.",
    "Classify the procedure example into its corresponding MITRE ATT&CK technique ID and name.",
    "Examine the procedure example and ascertain the appropriate MITRE ATT&CK technique ID and name.",
    "Evaluate the procedure example and assign the correct MITRE ATT&CK technique ID and name.",
    "Review the given procedure example and select the most relevant MITRE ATT&CK technique ID and name.",
    "Assess the procedure example and designate the fitting MITRE ATT&CK technique ID and name.",
    "Interpret the procedure example and determine the associated MITRE ATT&CK technique ID and name.",
]


def download_mitre():
    """
    Download the MITRE files
    """
    os.makedirs(mitre_folder, exist_ok=True)
    mitre_url = 'https://raw.githubusercontent.com/mitre/cti/ATT%26CK-v13.1/enterprise-attack/enterprise-attack.json'
    mitre_path = os.path.join(mitre_folder, 'enterprise-attack.json')
    urllib.request.urlretrieve(mitre_url, mitre_path)


def download_cve():
    """
    Download the CVE files
    """
    os.makedirs(cve_folder, exist_ok=True)
    cve_url = 'https://raw.githubusercontent.com/zefang-liu/cybersecurity-data/' \
        '7d77003027de028cd2daa25e5d03efd07ca09bd7/Global_Dataset.csv'
    cve_path = os.path.join(cve_folder, 'Global_Dataset.csv')
    urllib.request.urlretrieve(cve_url, cve_path)


def download_web():
    """
    Download the Web files
    """
    os.makedirs(web_folder, exist_ok=True)
    web_zip_url = 'https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/c2gw7fy2j4-3.zip'
    web_zip_path = os.path.join(web_folder, 'webpage_phising.zip')
    urllib.request.urlretrieve(web_zip_url, web_zip_path)
    shutil.unpack_archive(web_zip_path, web_folder)
    os.rename(
        os.path.join(
            web_folder, 'Web page phishing detection', 'dataset_B_05_2020.csv'),
        os.path.join(web_folder, 'dataset_phishing.csv'),
    )
    os.remove(web_zip_path)
    shutil.rmtree(os.path.join(web_folder, 'Web page phishing detection'))


def download_email():
    """
    Download the Email files
    """
    os.makedirs(email_folder, exist_ok=True)
    email_url = 'https://raw.githubusercontent.com/zefang-liu/cybersecurity-data/' \
        '7d77003027de028cd2daa25e5d03efd07ca09bd7/Phishing_Email.csv'
    email_path = os.path.join(email_folder, 'Phishing_Email.csv')
    urllib.request.urlretrieve(email_url, email_path)


def download_http():
    """
    Download the HTTP files
    """
    os.makedirs(http_folder, exist_ok=True)
    http_normal_train_url = 'https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/' \
        'c37152715bf95776bfb8d3430e38c3462914068a/OriginalDataSets/csic_2010/normalTrafficTraining.txt'
    http_normal_test_url = 'https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/' \
        'c37152715bf95776bfb8d3430e38c3462914068a/OriginalDataSets/csic_2010/normalTrafficTest.txt'
    http_anomalous_test_url = 'https://raw.githubusercontent.com/msudol/Web-Application-Attack-Datasets/' \
        'c37152715bf95776bfb8d3430e38c3462914068a/OriginalDataSets/csic_2010/anomalousTrafficTest.txt'
    http_normal_train_path = os.path.join(
        http_folder, 'normalTrafficTraining.txt')
    http_normal_test_path = os.path.join(http_folder, 'normalTrafficTest.txt')
    http_anomalous_test_path = os.path.join(
        http_folder, 'anomalousTrafficTest.txt')
    urllib.request.urlretrieve(http_normal_train_url, http_normal_train_path)
    urllib.request.urlretrieve(http_normal_test_url, http_normal_test_path)
    urllib.request.urlretrieve(
        http_anomalous_test_url, http_anomalous_test_path)


def clean_description(description):
    """
    Clean the procedure description
    """
    description_html = markdown(description)
    cleaned_description = re.sub(
        r"\s*\(Citation:[^)]+\)", "", BeautifulSoup(description_html, features="lxml").text)
    return cleaned_description


def load_mitre_data(mitre_attack_data):
    """
    Load the MITRE ATT&CK data
    """
    procedure_examples = []
    technique_descriptions = []
    techniques = mitre_attack_data.get_techniques(
        remove_revoked_deprecated=True)

    for technique in techniques:
        technique_stix_id = technique["id"]
        technique_id = mitre_attack_data.get_attack_id(
            stix_id=technique_stix_id)
        technique_name = technique["name"]

        if technique["x_mitre_is_subtechnique"]:
            parent_technique_name = mitre_attack_data.get_parent_technique_of_subtechnique(
                subtechnique_stix_id=technique_stix_id)[0]["object"]["name"]
            technique_name = f"{parent_technique_name}: {technique_name}"

        technique_descriptions.append({
            "technique_id": technique_id,
            "technique_name": technique_name,
            "technique_description": clean_description(technique["description"]),
        })

        attack_objects = []
        attack_objects.extend(mitre_attack_data.get_groups_using_technique(
            technique_stix_id=technique_stix_id))
        attack_objects.extend(mitre_attack_data.get_software_using_technique(
            technique_stix_id=technique_stix_id))
        attack_objects.extend(mitre_attack_data.get_campaigns_using_technique(
            technique_stix_id=technique_stix_id))

        for attack_object in attack_objects:
            relationship = attack_object["relationship"]
            description = relationship["description"]
            cleaned_description = clean_description(description)
            if cleaned_description.strip() != "":
                procedure_examples.append(
                    {"technique_id": technique_id, "procedure_description": cleaned_description})

    return pd.DataFrame(technique_descriptions), pd.DataFrame(procedure_examples)


def get_df_mitre():
    """
    Get the MITRE ATT&CK data
    """
    mitre_attack_data = MitreAttackData(
        os.path.join(mitre_folder, "enterprise-attack.json"))
    df_mitre_techniques, df_mitre_procedures = load_mitre_data(
        mitre_attack_data)
    df_mitre = df_mitre_procedures.merge(right=df_mitre_techniques, on='technique_id')[
        ['procedure_description', 'technique_id', 'technique_name']]
    df_mitre = df_mitre.drop_duplicates(
        subset=['procedure_description'], keep=False, ignore_index=True)

    # Drop techniques with frequencies less than 10
    technique_counts = df_mitre.technique_id.value_counts()
    selected_techniques = technique_counts[technique_counts >= 10].index
    df_mitre = df_mitre[df_mitre.technique_id.isin(
        selected_techniques)].reset_index(drop=True)

    df_mitre['input'] = df_mitre['procedure_description']
    df_mitre['output'] = df_mitre.apply(
        lambda row: row['technique_id'] + ' ' + row['technique_name'], axis='columns')
    df_mitre = df_mitre[['input', 'output']]

    df_mitre['task'] = 'tc'
    df_mitre['dataset'] = 'mitre'
    df_mitre = assign_instructions(
        df_mitre, outputs=None, instructions=mitre_instructions)
    df_mitre = drop_long_sequences(df_mitre)
    df_mitre = split_dataset(df_mitre, stratify=True)

    return df_mitre


cve_instructions = [
    "Based on the CVE description provided, determine the appropriate severity level: critical, high, medium, or low.",
    "Analyze the CVE description and classify its severity as either critical, high, medium, or low.",
    "Assess the given CVE description and indicate its severity class: critical, high, medium, or low.",
    "Examine the CVE description and assign it a severity rating of critical, high, medium, or low.",
    "Evaluate the provided CVE description and categorize it into one of the following severity levels: critical, high, medium, or low.",
    "Review the mentioned CVE description and identify its severity as critical, high, medium, or low.",
    "Study the CVE description and select the most accurate severity classification: critical, high, medium, or low.",
    "Inspect the given CVE description and establish its severity rating, choosing from critical, high, medium, or low.",
    "After reading the CVE description, decide the severity level and pick one: critical, high, medium, or low.",
    "From the CVE description, deduce the severity of the vulnerability and specify it as critical, high, medium, or low.",
]


def get_df_cve():
    """
    Get the CVE data
    """
    df_cve = pd.read_csv(os.path.join(cve_folder, 'Global_Dataset.csv'))
    df_cve = df_cve[df_cve['SEVERITY'] != 'None']
    df_cve = df_cve.drop_duplicates(
        subset='DESCRIPTION', keep='first', ignore_index=True)
    df_cve = df_cve[df_cve['CVE-ID'].str.slice(
        0, len('CVE-1999')) >= 'CVE-2021'].copy().reset_index()
    df_cve = df_cve.rename(columns={'DESCRIPTION': 'input', 'SEVERITY': 'output'})[
        ['input', 'output']]
    df_cve['output'] = df_cve['output'].str.lower()
    df_cve['task'] = 'tc'
    df_cve['dataset'] = 'cve'
    df_cve = assign_instructions(
        df_cve, outputs=['low', 'medium', 'high', 'critical'], instructions=cve_instructions)
    df_cve = drop_long_sequences(df_cve)
    df_cve = split_dataset(df_cve, stratify=True)
    return df_cve


web_instructions = [
    "Determine if the provided URL is phishing or legitimate.",
    "Analyze the given URL and classify it as either phishing or legitimate.",
    "Identify whether the following URL is part of a phishing attempt or a legitimate website.",
    "Examine the URL and categorize it as phishing or legitimate.",
    "Assess the URL and indicate if it belongs to a phishing scheme or a legitimate source.",
    "Evaluate the provided URL and label it as either a phishing attack or a legitimate site.",
    "Inspect the given URL and decide if it is associated with phishing or is a legitimate webpage.",
    "Review the URL and conclude if it is a phishing threat or a legitimate online destination.",
    "Scrutinize the URL and ascertain if it is part of a phishing scam or a legitimate website.",
    "Investigate the URL and deduce if it is related to a phishing operation or a legitimate internet source.",
]


def get_df_web():
    """
    Get the Web data
    """
    df_web = pd.read_csv(os.path.join(web_folder, 'dataset_phishing.csv'))
    df_web = df_web.drop_duplicates(subset=['url'], keep='first')
    df_web = df_web.rename(columns={'url': 'input', 'status': 'output'})[
        ['input', 'output']]
    df_web['task'] = 'tc'
    df_web['dataset'] = 'web'
    df_web = assign_instructions(
        df_web, outputs=['legitimate', 'phishing'], instructions=web_instructions)
    df_web = drop_long_sequences(df_web)
    df_web = split_dataset(df_web, stratify=True)
    return df_web


email_instructions = [
    "Identify if the given email is phishing or safe.",
    "Determine the classification of this email: phishing or safe.",
    "Classify this email as either phishing or safe.",
    "Analyze the email and decide if it is phishing or safe.",
    "Evaluate the email and provide the category: phishing or safe.",
    "Assess the email and select the appropriate label: phishing or safe.",
    "Inspect the email and indicate its classification: phishing or safe.",
    "Examine the email and classify it as phishing or safe.",
    "Review the email and decide on its category: phishing or safe.",
    "Analyze the email content and identify it as either phishing or safe.",
]


def get_df_email():
    """
    Get the Email data
    """
    df_email = pd.read_csv(os.path.join(
        email_folder, 'Phishing_Email.csv'), index_col=0)
    df_email = df_email.rename(
        columns={'Email Text': 'input', 'Email Type': 'output'})
    df_email = df_email[
        (~df_email.input.isna())
        & (df_email.input.str.strip() != '')
        & (df_email.input.str.lower().str.strip() != 'empty')
    ].reset_index(drop=True)
    df_email = df_email.drop_duplicates(
        subset='input', keep='first', ignore_index=True)
    df_email['output'] = df_email['output'].apply(
        lambda output: output.lower().replace('email', '').strip())

    df_email['task'] = 'tc'
    df_email['dataset'] = 'email'
    df_email = assign_instructions(
        df_email, outputs=['safe', 'phishing'], instructions=email_instructions)
    df_email = drop_long_sequences(df_email)
    df_email = split_dataset(df_email, stratify=True)
    return df_email


http_instructions = [
    "Determine if the given HTTP request is normal or anomalous.",
    "Classify the following HTTP request as either normal or anomalous.",
    "Identify the nature of this HTTP request: normal or anomalous.",
    "Assess the given HTTP request and categorize it as normal or anomalous.",
    "Analyze the provided HTTP request and indicate if it's normal or anomalous.",
    "Evaluate the HTTP request below and classify it as either normal or anomalous.",
    "Examine the HTTP request presented and decide if it's normal or anomalous.",
    "Review the specified HTTP request and ascertain if it's normal or anomalous.",
    "Inspect the HTTP request in question and determine its class: normal or anomalous.",
    "Appraise the accompanying HTTP request and designate it as normal or anomalous.",
]


def load_http_data(http_file_path, label):
    """
    Load the HTTP data
    """
    with open(http_file_path, 'r') as file:
        lines = file.read().splitlines()

    http_requests = [[]]

    for line in lines:
        if line.strip() == '':
            if http_requests[-1] != []:
                http_requests.append([])
        else:
            http_requests[-1].append(line)

    http_requests = [
        '\n'.join(http_request)
        for http_request in http_requests
        if len(http_request) > 1
    ]

    df_http = pd.DataFrame({
        'input': http_requests,
        'output': [label] * len(http_requests)
    })

    return df_http


def get_df_http():
    """
    Get the HTTP data
    """
    df_http_normal_test = load_http_data(os.path.join(
        http_folder, 'normalTrafficTest.txt'), 'normal')
    df_http_anomalous_test = load_http_data(os.path.join(
        http_folder, 'anomalousTrafficTest.txt'), 'anomalous')
    df_http = pd.concat(
        [df_http_normal_test, df_http_anomalous_test], ignore_index=True)
    df_http = df_http.sample(frac=0.2, replace=False,
                             random_state=0, ignore_index=True)
    df_http = df_http.drop_duplicates(subset='input', keep=False)
    df_http['task'] = 'tc'
    df_http['dataset'] = 'http'
    df_http = assign_instructions(
        df_http, outputs=['normal', 'anomalous'], instructions=http_instructions)
    df_http = drop_long_sequences(df_http)
    df_http = split_dataset(df_http, stratify=True)
    return df_http
