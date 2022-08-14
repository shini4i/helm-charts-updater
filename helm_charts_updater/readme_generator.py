from prettytable import MARKDOWN
from prettytable import PrettyTable


class Readme:
    def __init__(self):
        self.readme_path = "charts/README.md"
        self.readme_content = self._read_readme()

        self.table_start_marker = "<!-- table_start -->"
        self.table_end_marker = "<!-- table_end -->"

    def _read_readme(self) -> str:
        with open(self.readme_path, "r") as readme_file:
            return readme_file.read()

    @staticmethod
    def _generate_table(charts: list) -> PrettyTable:
        headers = ["Name", "Description", "Version", "App Version"]
        rows = []

        for chart in charts:
            rows.append(
                [
                    chart.name,
                    chart.description,
                    chart.version,
                    chart.appVersion,
                ]
            )

        table = PrettyTable(headers)
        table.set_style(MARKDOWN)
        table.add_rows(rows)

        return table

    def _replace_table(self, table: PrettyTable):
        print("===> Replacing table...")

        table_start = (
            self.readme_content.find(self.table_start_marker)
            + len(self.table_start_marker)
            + 1
        )
        table_end = self.readme_content.find(self.table_end_marker)

        if table_start == len(self.table_start_marker):
            raise IndexError("Table start marker not found")

        self.readme_content = (
            f"{self.readme_content[:table_start]}"
            f"{table.get_string()}\n"
            f"{self.readme_content[table_end:]}"
        )

    def update_readme(self, charts: list):
        table = self._generate_table(charts)

        self._replace_table(table)

        print("===> Writing new readme...")
        with open(self.readme_path, "w") as readme_file:
            readme_file.write(self.readme_content)
