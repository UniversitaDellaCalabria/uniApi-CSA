from datetime import datetime
import json
import requests
import urllib

CSA_API_CREDENTIALS = {
    "username": "thatuser",
    "password": "thatpassword"
}

CSA_API_URL = "https://prod.csa-ws.cineca.it/unical"
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
CSA_API_USER = "{}{}".format(CSA_API_BASE_URL, '/user')
CSA_API_RUOLI_LOC = "{}{}".format(CSA_API_BASE_URL, '/ruoliLocali')
CSA_API_PROF_LOC = "{}{}".format(CSA_API_BASE_URL, '/profiliLocali')
CSA_API_FUNZ = "{}{}".format(CSA_API_BASE_URL, '/funzioni')
CSA_API_NUM_FUNZ = "{}{}".format(CSA_API_BASE_URL, '/nominaFunzioni')


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

    def reset_password(self, password_old, password):
        req = requests.put(CSA_API_PASSWORD_REFRESH,
                           data={'password_old': password_old,
                                 'password': password})
        self.password = password
        return req

    @staticmethod
    def _fill_matricola(matricola):
        return str(matricola).zfill(6)

    def _get_headers(self):
        return {'Authorization': 'bearer {}'.format(self.token)}

    def auth(self):
        req = requests.post(CSA_API_AUTH_URL,
                            data=dict(username=self.username,
                                      password=self.password))
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
        if not rapporti: return False
        last_dt = datetime.strptime(rapporti[-1]['dataFine'], _strpformat)
        rapporto = {}
        for rap in rapporti:
            dt = datetime.strptime(rap['dataFine'], _strpformat)
            if dt >= last_dt:
                last_dt = dt
                rapporto = rap
        if datetime.now() < last_dt:
            return rapporto

    def sge_afforg(
            self, afferenzaOrganizzativa, dataInizio='01-01-1900', dataFine='01-01-2100',
            limit=50, offset=0
    ):
        """
        Il servizio, dato un’unità organizzativa e un intervallo di riferimento, restituisce l’elenco delle risorse
        umane che afferiscono all’unità organizzativa indicata, nell'intervallo temporale indicato.
        """

        params = dict(
            afferenzaOrganizzativa=afferenzaOrganizzativa, dataInizio=dataInizio,
            dataFine=dataFine, limit=limit, offset=offset
        )
        req = requests.get(CSA_API_SGE_AFFORG, params=params, headers=self._get_headers())
        return req.json()

    def sge_afforg_matricola(
            self, matricola, dataInizio='01-01-1900', dataFine='01-01-2100'):
        """
        Il servizio, data una risorsa umana identificata dalla matricola e un intervallo di riferimento temporale,
        restituisce l’elenco delle unità organizzative a cui afferisce la risorsa umana indicata.
        """
        url = '{}/{}?{}'.format(CSA_API_SGE_AFFORG,
                                self._fill_matricola(matricola),
                                urllib.parse.urlencode(dict(dataInizio=dataInizio,
                                                            dataFine=dataFine)))
        req = requests.get(url, headers=self._get_headers())
        return req.json()

    def sge_esp(self, matricola,
                dataRiferimento=None):
        """elenco afferenze organizzative per risorsa umana
           dato un periodo di riferimento
        """
        dataRiferimento = dataRiferimento or datetime.now().strftime('%m-%d-%Y')
        qs = urllib.parse.urlencode(dict(matricola=self._fill_matricola(matricola),
                                         dataRiferimento=dataRiferimento))
        url = '{}?{}'.format(CSA_API_SGE_ESP, qs)
        req = requests.get(url, headers=self._get_headers())
        return req.json()

    def funzioni(self):
        """
        Restituisce l'elenco di tutti i codici delle funzioni gestite dall'amministrazione dell'ateneo.
        """
        req = requests.get(CSA_API_FUNZ, headers=self._get_headers())
        return req.json()

    def nomina_funzioni(
            self, afferenzaOrganizzativa, matricola, funzione, dataInizio='01-01-1900', dataFine='01-01-2100',
            limit=50, offset=0
    ):
        """
        Restituisce l'elenco di risorse con la funzione attivita nell'intervallo passato come parametro

        """
        params = dict(
            afferenzaOrganizzativa=afferenzaOrganizzativa, matricola=matricola,
            funzione=funzione, dataInizio=dataInizio, dataFine=dataFine, limit=limit, offset=offset
        )
        req = requests.get(CSA_API_NUM_FUNZ, params=params, headers=self._get_headers())
        return req.json()

    def rapporti(
            self, dataInizio='01-01-1900', dataFine='01-01-2100',
            ruolo="", comparto="", limit=50, offset=0):
        """elenco di risorse con rapporto in essere nell' intervallo
        """
        params = dict(dataInizio=dataInizio, dataFine=dataFine, limit=limit, offset=offset)
        if ruolo:
            params['ruolo'] = ruolo
        if comparto:
            params['comparto'] = comparto

        req = requests.get(CSA_API_RAP,
                           params=params, headers=self._get_headers())
        return req.json()

    # TODO - Utente non autorizzato alla risorsa vociPersonaliGetAll
    def voci_personali(self, matricola, codice_esterno):
        """Restituisce una lista di voci personali corrispondenti
           ai parametri di ricerca. Occorre valorizzare almeno uno dei
           seguenti campi: idInterno, codEsterno, codFiscale, matricola
        """
        d = dict(matricola=matricola, codEsterno=codice_esterno)
        req = requests.get(CSA_API_VPER, params=d, headers=self._get_headers())
        return req.json()

    # TODO - Utente non autorizzato alla risorsa vociPersonaliGetAll
    def voci_variabili(self, matricola, codice_esterno):
        """Restituisce una lista di voci personali corrispondenti
           ai parametri di ricerca. Occorre valorizzare almeno uno dei
           seguenti campi: idInterno, codEsterno, codFiscale, matricola
        """
        d = dict(matricola=matricola, codEsterno=codice_esterno)
        req = requests.get(CSA_API_VVAR, params=d, headers=self._get_headers())
        return req.json()

    def ruoli_locali(self):
        """
        Restituisce l'elenco di tutti i ruoli locali e descrizioni utilizzati dall'ateneo.
        """
        req = requests.get(CSA_API_RUOLI_LOC, headers=self._get_headers())
        return req.json()

    def profili_locali(self):
        """
        Restituisce l'elenco di tutti i profili locali e descrizioni utilizzati dall'ateneo.
        """
        req = requests.get(CSA_API_PROF_LOC, headers=self._get_headers())
        return req.json()

    def admin_lista_utenti(self):
        """
        Estrae la lista degli utenti attivi per verificare l'accesso ai servizi
        """
        req = requests.get(CSA_API_USER, headers=self._get_headers())
        return req.json()

    def admin_dettaglio_utente(self, uid):
        """
        Estrae il dettaglio utente per tramite il paramentro path uid
        """
        csa_api_user_uid = "{}/{}".format(CSA_API_USER, uid)
        req = requests.get(csa_api_user_uid, headers=self._get_headers())
        return req.json()

    def admin_aggiungi_utente(self, data={}):
        """
        Estrae il dettaglio utente per tramite il paramentro path uid
        """
        req = requests.post(CSA_API_USER, json=data, headers=self._get_headers())
        return req


if __name__ == '__main__':
    csaconn = CsaConnect(CSA_API_BASE_URL,
                         **CSA_API_CREDENTIALS)
