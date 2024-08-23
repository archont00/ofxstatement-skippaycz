import csv
from datetime import datetime

from ofxstatement import statement
from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser

class SkippayczPlugin(Plugin):
    """Skip Pay s.r.o. (Czech Republic) (CSV, UTF-8 - exported from web app)
    """

    def get_parser(self, filename):
        SkippayczPlugin.encoding = self.settings.get('charset', 'utf-8-sig')
        f = open(filename, "r", encoding=SkippayczPlugin.encoding)
        parser = SkippayczParser(f)
        parser.statement.currency = self.settings.get('currency', 'CZK')
        parser.statement.bank_id = self.settings.get('bank', 'SkipPayCZ')
        parser.statement.account_id = self.settings.get('account', '')
        parser.statement.account_type = self.settings.get('account_type', 'CREDITLINE')
        parser.statement.trntype = "OTHER"
        return parser

class SkippayczParser(CsvStatementParser):

    date_format = '%d.%m.%Y'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)
        self.columns = None
        self.mappings = None

    def split_records(self):
        """Return iterable object consisting of a line per transaction
        """

        # Field delimiter may be dependent on user settings in mobile App (English/Czech)
        return csv.reader(self.fin, delimiter=';', quotechar='"')

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object
        """

        # First line of CSV file contains headers, not an actual transaction
        if self.cur_record == 1:
            # Prepare columns headers lookup table for parsing
            self.columns = {v: i for i,v in enumerate(line)}
            self.mappings = {
                "date": self.columns['Datum'],
                "memo": self.columns['Poznámka k úhradě'],
                "payee": self.columns['Obchodník'],
            }
            # And skip further processing by parser
            return None

        # Shortcut
        columns = self.columns

        # Normalize string. Better safe than sorry.
        for i,v in enumerate(line):
            line[i] = v.strip()

        # Convert numbers - thousands delimiter (special char: " " = "\xa") and decimal point
        if line[columns["částka"]] != '':
            line[columns["částka"]] = float(line[columns["částka"]].replace(' ', '').replace(',', '.').replace('Kč', ''))

        StatementLine = super(SkippayczParser, self).parse_record(line)

        # This is a liability account - negative amout is increase of debt, positive amount is repayment of loan
        StatementLine.amount = line[columns["částka"]] * -1

        StatementLine.id = statement.generate_transaction_id(StatementLine)

        # Manually set some of the typical transaction types.
        # EDIT: the bank is new, many types may be missing.
        payment_type = line[columns["Poznámka k úhradě"]]
        if payment_type.startswith("Platba vyúčtování"):
            StatementLine.trntype = "CREDIT"
        elif payment_type.startswith("Uplatněná odměna"):
            StatementLine.trntype = "CREDIT"
        elif payment_type.startswith("Dárkový poukaz"):
            StatementLine.trntype = "CREDIT"
        elif payment_type.startswith("100% sleva"):
            StatementLine.trntype = "CREDIT"
        elif payment_type.startswith("Platba kartou"):
            StatementLine.trntype = "POS"
        else:
            print("WARN: Unexpected type of payment appeared - \"{}\". Using XFER transaction type instead".format(payment_type))
            print("      Kindly inform the developer at https://github.com/archont00/ofxstatement-skippaycz/issues")
            StatementLine.trntype = "XFER"

        # .payee becomes OFX.NAME which becomes "Description" in GnuCash
        # .memo  becomes OFX.MEMO which becomes "Notes"       in GnuCash
        # When .payee is empty, GnuCash imports .memo to "Description" and keeps "Notes" empty

        # StatementLine.memo: include other useful info, if available

        if StatementLine.memo == "":
            separator = ""
        else:
            separator = "|"

        if line[columns["Poznámka k platbě kartou"]] != "None" and line[columns["Poznámka k platbě kartou"]] != "":
            StatementLine.memo += separator + line[columns["Poznámka k platbě kartou"]]
            separator = "|"

        return StatementLine
