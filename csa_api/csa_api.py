from datetime import datetime
import json
import requests
import urllib

CSA_API_CREDENTIALS = {
  "username": "thatuser",
  "password": "thatpassword"
}

CSA_API_URL = "https://prod.csa-ws.cineca.it/unicalProd"
CSA_API_TEST_URL = "https://preprod.csa-ws.cineca.it/unicalPreprod"

CSA_API_BASE_URL = CSA_API_TEST_URL
CSA_API_AUTH_URL = "{}{}".format(CSA_API_BASE_URL, '/authentication')
CSA_API_PASSWORD_REFRESH = "{}{}".format(CSA_API_BASE_URL,
                                         "/user/{username}/refreshPassword".format(**CSA_API_CREDENTIALS))

CSA_API_SGE_AFFORG = "{}{}".format(CSA_API_BASE_URL, '/sge/afferenzaOrganizzativa')
CSA_API_SGE_ESP = "{}{}".format(CSA_API_BASE_URL, '/sge/esposizioneSgePeriodo')
CSA_API_RAP = "{}{}".format(CSA_API_BASE_URL, '/rapporti')
CSA_API_VPER = "{}{}".format(CSA_API_BASE_URL, '/vociPersonali')
CSA_API_VVAR = "{}{}".format(CSA_API_BASE_URL, '/vociVariabili')


class CsaConnect(object):
    def __init__(self, base_url,
                       username=None,
                       password=None, token=None):
        self.username, self.password = username, password

        # if... handle token only without credentials
        self.token = token

        self.base_url = base_url
        self.tenant = base_url.rpartition('/')[-1]
        self.user = dict()

    @staticmethod
    def _fill_matricola(matricola):
        return str(matricola).zfill(6)

    def _get_headers(self):
        return {'Authorization': 'bearer {}'.format(self.token)}

    def auth(self):
        req = requests.post(CSA_API_AUTH_URL,
                            data=dict(username = self.username,
                                      password = self.password))
        data = json.loads(req.content.decode())
        # TODO
        assert 'code' not in data

        self.token = data['token']
        self.user = data['user']
        self.tenant = self.user['tenant']
        return self.user['verified']

    def attivo(self, matricola):
        _strpformat = '%Y-%m-%dT%H:%M:%S.000Z'
        rapporti = self.sge_afforg_matricola(matricola=matricola).get('list', [{}])
        last_dt = datetime.strptime(rapporti[-1]['dataFine'], _strpformat)
        rapporto = {}
        for rap in rapporti:
            dt = datetime.strptime(rap['dataFine'], _strpformat)
            if dt >= last_dt:
                last_dt = dt
                rapporto = rap
        if datetime.now() < last_dt:
            return rapporto

    def sge_afforg_matricola(self,
                             matricola,
                             dataInizio='01-01-1900',
                             dataFine='01-01-2100'):
        url = '{}/{}?{}'.format(CSA_API_SGE_AFFORG,
                             self._fill_matricola(matricola),
                             urllib.parse.urlencode(dict(dataInizio = dataInizio,
                                                         dataFine = dataFine))
                             )
        req = requests.get(url,
                           headers = self._get_headers())
        return req.json()


    def sge_esp(self, matricola,
                dataRiferimento=None):
        """elenco afferenze organizzative per risorsa umana
           dato un periodo di riferimento
        """
        dataRiferimento = dataRiferimento or datetime.now().strftime('%m-%d-%Y')
        qs = urllib.parse.urlencode(dict(matricola = self._fill_matricola(matricola),
                                         dataRiferimento = dataRiferimento))
        url = '{}?{}'.format(CSA_API_SGE_ESP, qs)
        req = requests.get(url, headers = self._get_headers())
        return req.json()

    def rapporti(self, dataInizio='01-01-1900',
                       dataFine='01-01-2100'):
        """elenco di risorse con rapporto in essere nell' intervallo
        """
        d = dict(dataInizio = dataInizio, dataFine = dataFine)
        req = requests.get(CSA_API_RAP, params = d, headers = self._get_headers())
        return req.json()


    # TODO - Utente non autorizzato alla risorsa vociPersonaliGetAll
    def voci_personali(self, matricola, codice_esterno):
        """Restituisce una lista di voci personali corrispondenti
           ai parametri di ricerca. Occorre valorizzare almeno uno dei
           seguenti campi: idInterno, codEsterno, codFiscale, matricola
        """
        d = dict(matricola = matricola, codEsterno = codice_esterno)
        req = requests.get(CSA_API_VPER, params = d, headers = self._get_headers())
        return req.json()

    # TODO - Utente non autorizzato alla risorsa vociPersonaliGetAll
    def voci_variabili(self, matricola, codice_esterno):
        """Restituisce una lista di voci personali corrispondenti
           ai parametri di ricerca. Occorre valorizzare almeno uno dei
           seguenti campi: idInterno, codEsterno, codFiscale, matricola
        """
        d = dict(matricola = matricola, codEsterno = codice_esterno)
        req = requests.get(CSA_API_VVAR, params = d, headers = self._get_headers())
        return req.json()


if __name__ == '__main__':
    csaconn = CsaConnect(CSA_API_BASE_URL,
                         **CSA_API_CREDENTIALS )
