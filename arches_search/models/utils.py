from pathlib import Path


# needs to be local - otherwise it'll path to arches core
def format_file_into_sql(file: str, sql_dir: str):
    sql_file = Path(__file__).parent / sql_dir / file
    sql_string = ""
    with open(sql_file) as file:
        sql_string = sql_string + "\n" + file.read()
    return sql_string
