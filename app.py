import pandas as pd
from datetime import datetime , date, timedelta
import math
import numpy as np
base_actif = pd.DataFrame()
base_retraite = pd.DataFrame()
base_conjoint = pd.DataFrame()
base_enfant = pd.DataFrame()
TFG=TFAQ =0.1 
TTass =0.14
age_retraite = 60
taux_actu = 0.02140
w = 110 #age limite
taux_remb = 0.8
taux_infm = 0.02
#CM=5000
alge=62 #L’âge jusqu’où on suppose que le salarié travaille
algc=65 #L’âge jusqu’où les prestations sociales sont versées/couvertes
chrev = 0,39
chft = 0.39819
chrev = (((1+TFG)/(1-TFAQ))*(1+ TTass)) - 1 


class Personne:
    def __init__ (self, matricule: str, date_naissance: date, date_embauche: date = None, salaire: float=None):
        if not isinstance(matricule,str):
            raise TypeError("le matricule doit etre un chaine de caratère")
        if not isinstance(date_naissance,date):
            raise TypeError("veuillez saisir une date correcte")
        if date_embauche is not None and not isinstance(date_embauche,date):
            raise TypeError("veuillez saisir une date dorrecte")
        if salaire is not None and not isinstance(salaire, float):
            raise TypeError("le salaire doit etre un nombre")
        self.matricule = matricule
        self.date_naissance = date_naissance
        self.date_embauche = date_embauche 
        self.salaire = salaire
    def afficher (self):
        print(f"matricule :{self.matricule}, Date de naissance: {self.date_naissance}, Date d'embauche: {self.date_embauche}, Salaire: {self.salaire}")
    def age (self):
        age_ = date.today().year - self.date_naissance.year
        if (date.today().month, date.today().day) < (self.date_naissance.month, self.date_naissance.day):
            age_ -= 1
        return age_
    def anciennete_actuelle (self):
        result = date.today() - self.date_embauche
        return result.days // 365
    def anciennete_terme(self, age_retraite=60):
        annee_retraite = self.date_naissance.year + age_retraite
        try:
            date_retraite = date(annee_retraite, self.date_naissance.month, self.date_naissance.day)
        except ValueError:
            date_retraite = date(annee_retraite, 3, 1)
        anciennete = date_retraite - self.date_embauche
        return anciennete.days // 365
    def prorata (self,age_retraite=60):
        return self.anciennete_actuelle()/self.anciennete_terme(age_retraite=60)
    def prori(self, i: int): 
        anciennete = (date.today() - self.date_embauche).days / 365.25  # float en années
        age_decimal = (self.date_embauche - self.date_naissance).days / 365.25  # float en années
        denominateur = (self.age() + i) - age_decimal
        pror_ = anciennete / denominateur
        return pror_
    def pror(self):
        anciennete = (date.today() - self.date_embauche).days / 365.25  # float en années
        age_decimal = (date.today() - self.date_naissance).days / 365.25  # float en années
        denominateur = age_retraite - age_decimal
        pror_ = anciennete / denominateur
        return pror_
    

table = pd.read_excel("Table de mortalite - IAS19.xlsx", header= 1)
def lx(personne):
    return table.loc[table["AGE"]==personne.age(),"lx"].iloc[0]

def rpx(personne:Personne, r):
    x = personne.age() + r
    return table["lx"][personne.age()+r]/lx(personne)


def turn_over(personne:Personne):
    if((personne.age()>=20 and personne.age()<=30) or (personne.age()>=56 and personne.age()<=60)):
        to = 0
    elif(personne.age()>=31 and personne.age()<=35):
        to = 0.0063
    elif(personne.age()>=36 and personne.age()<=40):
        to = 0.0051
    elif(personne.age()>=41 and personne.age()<=45):
        to = 0.0057
    elif(personne.age()>=46 and personne.age()<=50):
        to = 0.0066
    elif(personne.age()>=51 and personne.age()<=55):
        to = 0.0072
    return to


def ifc(personne:Personne,choix:int):
    if ( choix ==1 ):
        if (personne.anciennete_terme() <= 5):
            ifc_ = 0.45 * personne.salaire
        elif (6 <= personne.anciennete_terme() <= 10):
            ifc_ = 0.50 * personne.salaire
        else :
            ifc_ = 0.60 * personne.salaire
    elif ( choix == 2 or choix == 3 ) :
        if (personne.anciennete_terme() <= 5):
            ifc_ = 0.35 * personne.salaire
        elif (6 <= personne.anciennete_terme() <= 10):
            ifc_ = 0.40 * personne.salaire
        else :
            ifc_ = 0.45 * personne.salaire
    return ifc_


def cp(personne:Personne):
    chargement = 0.22789
    return personne.salaire * chargement + min(0.0805*personne.salaire , 144000) + min(0.0898*personne.salaire , 72000)



def ajouter_age(personne: Personne, nb_annees: int):
    try:
        nouvelle_date_naissance = personne.date_naissance.replace(
            year=personne.date_naissance.year - nb_annees
        )
    except ValueError:
        nouvelle_date_naissance = personne.date_naissance + timedelta(days=365 * nb_annees)

    cls = personne.__class__
    attrs = personne.__dict__.copy()
    attrs["date_naissance"] = nouvelle_date_naissance

    if cls.__name__ == "Actif":
        attrs.pop("salaire", None)   # Actif n’a pas salaire
        attrs.pop("statut", None)
    if cls.__name__ == "Retraite":
        attrs.pop("salaire", None)
        #attrs.pop("statut", None)
        attrs.pop("date_embauche", None)
    if cls.__name__ in ["Conjoint", "Enfant"]:
        attrs.pop("date_embauche", None)  # Ces classes n’ont pas date_embauche
        attrs.pop("salaire", None)        # Ni salaire

    return cls(**attrs)



def PBO(personne:Personne, choix)-> float:
    if(choix == "Cas en sortie de retraite"):
        proba = 1
        for i in range (personne.age(), age_retraite+1):
            proba = proba * (1 - turn_over(ajouter_age(personne , i-personne.age())))
        PBO_ = proba * rpx(personne, age_retraite - personne.age()) * ((1 / ((1 + taux_actu) ** (age_retraite - personne.age()))) * (ifc(personne,1) + cp(personne)) * personne.prorata())
    elif(choix == "Cas de démission"):
        somme = 0
        for i in range (1, age_retraite - personne.age()):
            proba = 1
            for j in range(1, i + 1 ):
                proba = proba * (1- turn_over(ajouter_age(personne, j-1)))
            somme = somme + ( proba * rpx(personne, i) * turn_over(ajouter_age(personne,i)) *  (1/((1+taux_actu)**i)) *(ifc(personne,2) + cp(personne)) * personne.prorata(i))
        PBO_ = somme
    elif(choix == "Cas de décès"):
        somme = 0
        for i in range (1, age_retraite - personne.age()):
            proba = 1
            for j in range(1, i + 1 ):
                proba = proba * (1- turn_over(ajouter_age(personne, j-1)))
            somme = somme + ( proba * rpx(personne, i) * (1-rpx(ajouter_age(personne,i),1)) *  (1/((1+taux_actu)**i)) *(ifc(personne,3) + cp(personne)) * personne.prorata(i))
        PBO_ = somme
    else:
        raise TypeError("le choix est invalide")
    return PBO_



def SC(personne:Personne, choix:int):
    if (choix == 1 ):
        sc_ = PBO(personne,1)/personne.anciennete_actuelle()
    elif(choix == 2) :
        sc_ = PBO(personne,2)/personne.anciennete_actuelle()
    else:
        sc_ = PBO(personne,3)/personne.anciennete_actuelle()
        
    return sc_

#****************
#dfa = pd.read_excel("input_Actifs.xlsx")
#dfr = pd.read_excel("input_Retraités.xlsx")
#dfca = pd.read_excel("input_Conjoint actif.xlsx")
#dfcr = pd.read_excel("input_Conjoint retraité.xlsx")
#dfea = pd.read_excel("input_Enfant actif.xlsx")
#dfer = pd.read_excel("input_Enfant retraité.xlsx")
#data_actif = df1.merge(df3, on = "Matricule", how ="left").merge(df5, on="Matricule", how="left")
#data_retraite = df2.merge(df4, on = "Matricule", how ="left").merge(df6, on="Matricule", how="left")
dfcm = pd.read_excel("Courbe de consommation actif & retraité.xlsx")
dfcme = pd.read_excel("Courbe de consommation Enfant.xlsx")
dfcmc = pd.read_excel("Courbe de consommation Conjoint.xlsx")

#dfa.columns = ["matricule", "date_naissance", "date_embauche", "categorie"]
#dfr.columns = ["matricule", "date_naissance", "statut"]
#dfca.columns = ["matricule", "date_naissance"]
#dfcr.columns = ["matricule", "date_naissance"]
#dfea.columns = ["matricule", "date_naissance"]
#dfer.columns = ["matricule", "date_naissance"]
dfcm.columns = ["age", "consommation_medicale"]
dfcmc.columns = ["age", "consommation_medicale"]
dfcme.columns = ["age", "consommation_medicale"]

# Dans app.py
class Actif(Personne):
    def __init__(self, matricule: str, date_naissance: date, date_embauche: date, categorie: str,
                 statut: str = None, base_conjoint_=None, base_enfant_=None):
        super().__init__(matricule, date_naissance, date_embauche, salaire=None)
        self.categorie = categorie
        self.base_conjoint_ = base_conjoint_
        self.base_enfant_ = base_enfant_

    @property
    def conjoint(self):
        if self.categorie not in ["Marié(e)", "Marié", "marie", "MARIÉ"]:
            return None
        if self.base_conjoint_ is None:
            return None
        row = self.base_conjoint_.loc[self.base_conjoint_["matricule"] == self.matricule]
        if not row.empty:
            c = row.iloc[0]
            return Conjoint(c["matricule"], c["date_naissance"])
        return None

    @property
    def enfant(self):
        if self.base_enfant_ is None:
            return None
        row = self.base_enfant_.loc[self.base_enfant_["matricule"] == self.matricule]
        if not row.empty:
            c = row.iloc[0]
            return Enfant(c["matricule"], c["date_naissance"])
        return None


class Retraite(Personne):
    def __init__(self, matricule: str, date_naissance: date, statut: str,
                 base_conjoint_=None, base_enfant_=None):
        super().__init__(matricule, date_naissance, date_embauche=None, salaire=None)
        self.statut = statut
        self.base_conjoint_ = base_conjoint_
        self.base_enfant_ = base_enfant_

    @property
    def conjoint(self):
        if self.statut not in ["Marié(e)", "Marié", "marie", "MARIÉ"]:
            return None
        if self.base_conjoint_ is None:
            return None
        row = self.base_conjoint_.loc[self.base_conjoint_["matricule"] == self.matricule]
        if not row.empty:
            c = row.iloc[0]
            return Conjoint(c["matricule"], c["date_naissance"])
        return None

    @property
    def enfant(self):
        if self.base_enfant_ is None:
            return None
        row = self.base_enfant_.loc[self.base_enfant_["matricule"] == self.matricule]
        if not row.empty:
            c = row.iloc[0]
            return Enfant(c["matricule"], c["date_naissance"])
        return None
class Enfant:
    def __init__(self, matricule: str, date_naissance: date):
        self.matricule = matricule
        self.date_naissance = date_naissance

    def age(self):
        return (date.today() - self.date_naissance).days // 365

class Conjoint:
    def __init__(self, matricule: str, date_naissance: date):
        self.matricule = matricule
        self.date_naissance = date_naissance

    def age(self):
        return (date.today() - self.date_naissance).days // 365


def cm(personne: Personne):
    if isinstance(personne, (Actif, Retraite)):
        df = dfcm
    elif isinstance(personne, Conjoint):
        df = dfcmc
    elif isinstance(personne, Enfant):
        df = dfcme
    else:
        raise TypeError("Objet non reconnu")

    age = personne.age()
    if age in df["age"].values:
        return df.loc[df["age"] == age, "consommation_medicale"].iloc[0]
    df_sorted = df.sort_values("age").reset_index(drop=True)
    cm_interp = np.interp(age, df_sorted["age"], df_sorted["consommation_medicale"])
    return cm_interp


#**********VAP
def EPP(personne:Personne, i:int):
    if isinstance(personne, Actif):
        epp = (
            rpx(ajouter_age(personne, age_retraite - personne.age()), i)
            * cm(ajouter_age(personne, age_retraite - personne.age() + i))
            * ((1 + taux_infm) ** i)
            * taux_remb
        )
    elif isinstance(personne, Retraite):
        epp = (
            rpx(personne, i)
            * cm(ajouter_age(personne, i))
            * ((1 + taux_infm) ** i)
            * taux_remb
            )
    else:
        epp = "Pas actif, ni retraité"
    return epp

def VAPP(personne:Personne):
    if isinstance(personne, Actif):
        proba = 1
        for k in range(personne.age(), age_retraite):
            proba = proba * (1 - turn_over(ajouter_age(personne, k - personne.age())))
        somme = 0
        for i in range(w - age_retraite + 1):
            somme += EPP(personne, i) / ((1 + taux_actu) ** i)
        divi = ((1 + taux_infm) ** (age_retraite - personne.age())) / ((1 + taux_actu) ** (age_retraite - personne.age()))
        vapp = divi * proba * personne.prorata() * rpx(personne, age_retraite - personne.age()) * somme
    elif isinstance(personne, Retraite):
        somme = 0
        for i in range(w - age_retraite + 1):
            somme += EPP(personne, i) / ((1 + taux_actu) ** i)
        vapp = somme
    else:
        vapp = "pas actif ni retraité"
    return vapp

def VAP(personne:Personne): 
    vap = 0
    for j in range(age_retraite - personne.age()):
        vap += VAPP(ajouter_age(personne, j))
    return vap

#**********VAPRF
def VAPRCA1(personne:Personne):
    if isinstance(personne, Actif):
        vaprca1 = 0
        for i in range(age_retraite - personne.age()):
            somme2 = 0
            if personne.conjoint.age() + i > algc:
                somme2 = 0
            else:
                coefe = 0
                for j in range(algc - (personne.conjoint.age()+i)):
                    somme1 = 0
                    if personne.conjoint.age() + i + j > algc:
                        somme1 = 0
                    else:
                        somme1 = (
                            cm(ajouter_age(personne.conjoint, i + j))
                            * (lx(ajouter_age(personne.conjoint, i + j + 1)) / lx(ajouter_age(personne.conjoint, i)))
                            * math.sqrt(lx(ajouter_age(personne.conjoint, i + j)) / lx(ajouter_age(personne.conjoint, i)))
                            * ((1 + taux_infm) ** (j + 0.5))
                            * ((1 + chft) / ((1 + taux_actu) ** (j + 0.5)))
                        )
                    coefe = coefe + somme1
                proba = 1
                for k in range(personne.age(), personne.age() + i + 1):
                    proba = proba * (1 - turn_over(ajouter_age(personne, k - personne.age())))
                somme2 = (
                    coefe
                    * (((1 + taux_infm) / (1 + taux_actu)) ** i)
                    * (lx(ajouter_age(personne, i)) / lx(personne))
                    * (lx(ajouter_age(personne.conjoint, i)) / lx(personne.conjoint))
                    * ((lx(ajouter_age(personne, i)) - lx(ajouter_age(personne, i + 1))) / lx(ajouter_age(personne, i)))
                    * personne.prori(i)
                    * proba
                )
            vaprca1 = vaprca1 + somme2
    else:
        raise TypeError("Pas actif")
    return vaprca1

def VAPRCA2(personne:Personne):
    if isinstance(personne, Actif):
        vaprca2 = 0
        for i in range(algc - age_retraite):
            somme2 = 0
            if (personne.conjoint.age() + (age_retraite + i - personne.age()) > algc):
                somme2 = 0
            else:
                coefa = 0
                for j in range(algc - (personne.conjoint.age() + (age_retraite + i - personne.age())) + 1):
                    somme1 = 0
                    if (personne.conjoint.age() + (age_retraite + i - personne.age()) + j > algc):
                        somme1 = 0
                    else:
                        somme1 = (
                            cm(ajouter_age(personne.conjoint, (age_retraite + i - personne.age()) + j))
                            * (lx(ajouter_age(personne.conjoint, (age_retraite + i - personne.age()) + j))
                               / lx(ajouter_age(personne.conjoint, (age_retraite + i - personne.age()))))
                            * math.sqrt(
                                lx(ajouter_age(personne.conjoint, (age_retraite + i - personne.age()) + j + 1))
                                / lx(ajouter_age(personne.conjoint, (age_retraite + i - personne.age())))
                            )
                            * ((1 + taux_infm) ** (j + 0.5))
                            * ((1 + chft) / ((1 + taux_actu) ** (j + 0.5)))
                        )
                    coefa = coefa + somme1               
                somme2 = (
                    coefa
                    * (((1 + taux_infm) / (1 + taux_actu)) ** (age_retraite + i - personne.age()))
                    * (lx(ajouter_age(personne, (age_retraite + i - personne.age()))) / lx(personne))
                    * (lx(ajouter_age(personne.conjoint, (age_retraite + i - personne.age()))) / lx(personne.conjoint))
                    * ((lx(ajouter_age(personne, (age_retraite + i - personne.age()))) - lx(ajouter_age(personne, (age_retraite + i - personne.age() + 1))))
                       / lx(ajouter_age(personne, i)))
                )
            vaprca2 = vaprca2 + somme2
        proba = 1
        for k in range(personne.age(), age_retraite):
            proba = proba * (1 - turn_over(ajouter_age(personne, k - personne.age())))
        vaprca2_ = vaprca2 * personne.pror() * proba
    else:
        raise TypeError("Pas actif")
    return vaprca2_

def VAPRCR(personne: Personne):
    if isinstance(personne, Retraite):
        vaprcr = 0
        for i in range(w - personne.age()):
            somme2 = 0
            if (personne.conjoint.age() + i > algc):
                somme2 = 0
            else:
                coefb = 0
                for j in range(algc - (personne.conjoint.age() + i) + 1):
                    somme1 = 0
                    if (personne.conjoint.age() + i + j > algc):
                        somme1 = 0
                    else:
                        somme1 = (
                            cm(ajouter_age(personne.conjoint, i + j))
                            * (lx(ajouter_age(personne.conjoint, i + j)) / lx(ajouter_age(personne.conjoint, i)))
                            * math.sqrt(
                                lx(ajouter_age(personne.conjoint, i + j)) / lx(ajouter_age(personne.conjoint, i))
                            )
                            * ((1 + taux_infm) ** (j + 0.5))
                            * ((1 + chft) / ((1 + taux_actu) ** (j + 0.5)))
                        )
                    coefb = coefb + somme1
                somme2 = (
                    coefb
                    * (((1 + taux_infm) / (1 + taux_actu)) ** i)
                    * (lx(ajouter_age(personne, i)) / lx(personne))
                    * (lx(ajouter_age(personne.conjoint, i)) / lx(personne.conjoint))
                    * ((lx(ajouter_age(personne, i)) - lx(ajouter_age(personne, i + 1))) / lx(ajouter_age(personne, i)))
                )
            vaprcr = vaprcr + somme2
    else:
        raise TypeError("Pas actif")
    return vaprcr
    
def VAPREA1(personne:Personne):
    if isinstance(personne, Actif):
        vaprea1 = 0
        for i in range(age_retraite - personne.age()):
            somme2 = 0
            if (personne.enfant.age() + i > alge):
                somme2 = 0
            else:
                coeff = 0
                for j in range(alge - (personne.enfant.age() + i ) + 1):
                    somme1 = 0
                    if (personne.enfant.age() + i + j > alge):
                        somme1 = 0
                    else:
                        somme1 = (
                            cm(ajouter_age(personne.enfant, i + j))
                            * (lx(ajouter_age(personne.enfant, i + j)) / lx(ajouter_age(personne.enfant, i)))
                            * math.sqrt(
                                lx(ajouter_age(personne.enfant, i + j + 1)) / lx(ajouter_age(personne.enfant, i))
                            )
                            * ((1 + taux_infm) ** (j + 0.5))
                            * ((1 + chft) / ((1 + taux_actu) ** (j + 0.5)))
                        )
                    coeff = coeff + somme1
                somme2 = (
                    coeff
                    * (((1 + taux_infm) / (1 + taux_actu)) ** i)
                    * (lx(ajouter_age(personne, i)) / lx(personne))
                    * (lx(ajouter_age(personne.enfant, i)) / lx(personne.enfant))
                    * ((lx(ajouter_age(personne, i)) - lx(ajouter_age(personne, i + 1))) / lx(ajouter_age(personne, i)))
                )
            vaprea1 = vaprea1 + somme2
        proba = 1
        for k in range(personne.age(), age_retraite):
            proba = proba * (1 - turn_over(ajouter_age(personne, k - personne.age())))
        vaprea1_ = vaprea1 * personne.pror() * proba
        return vaprea1_
    else:
        raise TypeError("Pas actif")

def VAPREA2(personne:Personne):
    if isinstance(personne, Actif):
        vaprea2 = 0
        for i in range(w - age_retraite):
            somme2 = 0
            if (personne.enfant.age() + (age_retraite - personne.age() + i) > alge):
                somme2 = 0
            else:
                coefc = 0
                for j in range(alge - (personne.enfant.age() + (age_retraite - personne.age() + i) ) + 1):
                    somme1 = 0
                    if (personne.enfant.age() + (age_retraite - personne.age() + i) + j > alge):
                        somme1 = 0
                    else:
                        somme1 = (
                            cm(ajouter_age(personne.enfant, (age_retraite - personne.age() + i) + j))
                            * (lx(ajouter_age(personne.enfant, (age_retraite - personne.age() + i) + j)) / lx(ajouter_age(personne.enfant, (age_retraite - personne.age() + i))))
                            * math.sqrt(
                                lx(ajouter_age(personne.enfant, (age_retraite - personne.age() + i) + j + 1)) / lx(ajouter_age(personne.enfant, (age_retraite - personne.age() + i)))
                            )
                            * ((1 + taux_infm) ** (j + 0.5))
                            * ((1 + chft) / ((1 + taux_actu) ** (j + 0.5)))
                        )
                    coefc = coefc + somme1
                somme2 = (
                    coefc
                    * (((1 + taux_infm) / (1 + taux_actu)) ** (age_retraite - personne.age() + i))
                    * (lx(ajouter_age(personne, age_retraite - personne.age() + i)) / lx(personne))
                    * (lx(ajouter_age(personne.enfant, (age_retraite - personne.age() + i))) / lx(personne.enfant))
                    * ((lx(ajouter_age(personne, age_retraite - personne.age() + i)) - lx(ajouter_age(personne, age_retraite - personne.age() + i + 1))) / lx(ajouter_age(personne, age_retraite - personne.age() + i)))
                )
            vaprea2 = vaprea2 + somme2
        proba = 1
        for k in range(personne.age(), age_retraite):
            proba = proba * (1 - turn_over(ajouter_age(personne, k - personne.age())))
        vaprea2_ = vaprea2 * personne.pror() * proba
    else:
        raise TypeError("Pas actif")
    return vaprea2_

def VAPRER(personne: Personne):
    if isinstance(personne, Retraite):
        vaprer = 0
        for i in range(w - personne.age()):
            somme2 = 0
            if (personne.enfant.age() + i > alge):
                somme2 = 0
            else:
                coefd = 0
                for j in range(algc - (personne.enfant.age() + i) + 1):
                    somme1 = 0
                    if (personne.enfant.age() + i + j > alge):
                        somme1 = 0
                    else:
                        somme1 = (
                            cm(ajouter_age(personne.enfant, i + j))
                            * (lx(ajouter_age(personne.enfant, i + j)) / lx(ajouter_age(personne.enfant, i)))
                            * math.sqrt(
                                lx(ajouter_age(personne.enfant, i + j)) / lx(ajouter_age(personne.enfant, i))
                            )
                            * ((1 + taux_infm) ** (j + 0.5))
                            * ((1 + chft) / ((1 + taux_actu) ** (j + 0.5)))
                        )
                    coefd = coefd + somme1
                somme2 = (
                    coefd
                    * (((1 + taux_infm) / (1 + taux_actu)) ** i)
                    * (lx(ajouter_age(personne, i)) / lx(personne))
                    * (lx(ajouter_age(personne.enfant, i)) / lx(personne.enfant))
                    * ((lx(ajouter_age(personne, i)) - lx(ajouter_age(personne, i + 1))) / lx(ajouter_age(personne, i)))
                )
            vaprer = vaprer + somme2
    else:
        raise TypeError("Pas actif")
    return vaprer
def VAPRE (personne:Personne):
    if personne.enfant is None:
        vapre = 0
    else :
        if isinstance(personne,Actif):
            vapre = VAPREA1(personne) + VAPREA2(personne)
        elif isinstance(personne,Retraite):
            vapre = VAPRER(personne)
        else:
            vapre = "Pas actif, ni retraite"
    return vapre

def VAPRC (personne:Personne):
    if personne.conjoint is None:
        vaprc = 0
    else :
        if isinstance(personne,Actif):
            vaprc = VAPRCA1(personne) + VAPRCA2(personne)
        elif isinstance(personne,Retraite):
            vaprc = VAPRCR(personne)
        else:
            vaprc = "Pas actif, ni retraite"
    return vaprc

def VAPRF(personne:Personne, cas=2):
    if(cas == 1):
        vaprf = VAPP(personne)*chrev
    elif(cas == 2):
        vaprf = VAPRC(personne) + VAPRE(personne)
    return vaprf
    
#**********PBO    
def PBO_(personne:Personne):
    return round (VAP(personne) + VAPRF(personne))

