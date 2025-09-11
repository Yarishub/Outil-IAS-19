import streamlit as st 
import pandas as pd
from app import * 
st.markdown(
    """
    <style>
    .stApp {
        background-color: #E6F2FF;
        color: #0A0A0A;
    }

    h1 {
        color: #004080;
    }

    .stButton>button {
        background-color: #004080;
        color: white;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

age_retraite = 60

st.set_page_config(
    page_title="IAS 19 - Engagements Sociaux",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Calcul des engagements sociaux selon IAS 19")
st.markdown("---")

st.sidebar.title("⚙️ Paramètres")
choix = st.sidebar.radio(
    "Choisissez le type d'engagement :",
    ("Indemnités de Fin de Carrière (IFC)", "Consommations Médicales (CM)")
)

st.write(f"### Vous avez choisi : **{choix}**")

# ======================= IFC =======================
if choix == "Indemnités de Fin de Carrière (IFC)":
    st.subheader("🧮 Saisie des variables pour l'IFC")
    col1, col2 = st.columns(2)
    with col1:
        age_retraite = st.number_input("Âge de retraite", min_value=0, max_value=120, value=60)
    with col2:
        uploaded_file = st.file_uploader("📂 Chargez la base de données pour IFC", type=["csv","xlsx"])

    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
            else:
                df = pd.read_excel(uploaded_file)

            st.success("✅ Fichier chargé avec succès !")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du fichier : {e}")

        sous_choix = st.selectbox(
            "📌 Choisissez le cas pour le calcul de l'IFC",
            ("Cas en sortie de retraite", "Cas de démission", "Cas de décès")
        )
        st.info(f"➡️ Vous avez choisi : **{sous_choix}**")

        if st.button("🚀 Calculer les engagements"):
            df = df.rename(columns={
                "Numéro Identifiant du salarié": "matricule",
                "date de naissance": "date_naissance",
                "date d'embauche à la société": "date_embauche",
                "salaire annuel assiette de chaque prestation constituant l'avantage": "salaire"
            })

            df["date_naissance"] = pd.to_datetime(df["date_naissance"], errors="coerce").dt.date
            df["date_embauche"] = pd.to_datetime(df["date_embauche"], errors="coerce").dt.date

            resultats = []
            for _, row in df.iterrows():
                p = Personne(**row.to_dict())
                engagement = PBO(p, sous_choix)
                resultats.append(engagement)

            df["Engagement"] = resultats
            st.success("✅ Calcul terminé !")
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Télécharger les résultats en CSV", csv, "resultats_ifc.csv", "text/csv")

# ======================= CM =======================
elif choix == "Consommations Médicales (CM)": 
    st.subheader("🩺 Saisie des variables pour les CM")

    col1, col3 = st.columns(2)
    with col1:
        age_retraite = st.number_input("Age de la retraite", min_value=0)
    with col3:
        TFG = st.number_input("⚖️ Taux de frais de gestion", min_value=0.0, max_value=1.0, value=0.1, step=0.01)

    col4, col5, col6 = st.columns(3)
    with col4:
        TFAQ = st.number_input("📊 Taux de frais d'acquisition", min_value=0.0, max_value=1.0, value=0.1, step=0.01)
    with col5:
        TTass = st.number_input("💵 Taux de taxe assureur", min_value=0.0, max_value=1.0, value=0.14, step=0.01)
    with col6:
        choix_employé = st.radio("👥 Base :", ("Actifs", "Retraités"))

    st.info(f"➡️ Vous avez choisi : **{choix_employé}**")

    if choix_employé == "Actifs":
        uploaded_file_actif = st.file_uploader("📂 Base des Actifs", type=["csv","xlsx"])
        uploaded_file_conjoint = st.file_uploader("📂 Base des Conjoints", type=["csv","xlsx"])
        uploaded_file_enfant = st.file_uploader("📂 Base des Enfants", type=["csv","xlsx"])

        if uploaded_file_actif and uploaded_file_conjoint and uploaded_file_enfant:
            if st.button("🚀 Calculer les engagements"):
                base_actif = pd.read_excel(uploaded_file_actif)
                base_conjoint = pd.read_excel(uploaded_file_conjoint)
                base_enfant = pd.read_excel(uploaded_file_enfant)

                base_actif.columns = ["matricule", "date_naissance", "date_embauche", "categorie"]
                base_conjoint.columns = ["matricule", "date_naissance"]
                base_enfant.columns = ["matricule", "date_naissance"]

                base_actif["date_naissance"] = pd.to_datetime(base_actif["date_naissance"], errors="coerce").dt.date
                base_actif["date_embauche"] = pd.to_datetime(base_actif["date_embauche"], errors="coerce").dt.date
                base_conjoint["date_naissance"] = pd.to_datetime(base_conjoint["date_naissance"], errors="coerce").dt.date
                base_enfant["date_naissance"] = pd.to_datetime(base_enfant["date_naissance"], errors="coerce").dt.date

                resultats = []
                for _, row in base_actif.head(10).iterrows():
                    p = Actif(
                        matricule=row["matricule"],
                        date_naissance=row["date_naissance"],
                        date_embauche=row["date_embauche"],
                        categorie=row["categorie"],
                        base_conjoint_=base_conjoint,
                        base_enfant_=base_enfant
                    )
                    engagement = PBO_(p)
                    resultats.append(engagement)

                base_actif.loc[base_actif.head(10).index, "Engagement"] = resultats
                st.success("✅ Calcul terminé ! (aperçu sur 10 lignes)")
                st.dataframe(base_actif.head(10))

                csv = base_actif.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Télécharger les résultats en CSV", csv, "resultats_cm.csv", "text/csv")


    else:
        uploaded_file_actif = st.file_uploader("📂 Base des Retraités", type=["csv","xlsx"])
        uploaded_file_conjoint = st.file_uploader("📂 Base des Conjoints", type=["csv","xlsx"])
        uploaded_file_enfant = st.file_uploader("📂 Base des Enfants", type=["csv","xlsx"])

        if uploaded_file_actif and uploaded_file_conjoint and uploaded_file_enfant:
            if st.button("🚀 Calculer les engagements"):
                base_actif = pd.read_excel(uploaded_file_actif)
                base_conjoint = pd.read_excel(uploaded_file_conjoint)
                base_enfant = pd.read_excel(uploaded_file_enfant)

                base_actif.columns = ["matricule", "date_naissance", "statut"]
                base_conjoint.columns = ["matricule", "date_naissance"]
                base_enfant.columns = ["matricule", "date_naissance"]

                base_actif["date_naissance"] = pd.to_datetime(base_actif["date_naissance"], errors="coerce").dt.date
                base_conjoint["date_naissance"] = pd.to_datetime(base_conjoint["date_naissance"], errors="coerce").dt.date
                base_enfant["date_naissance"] = pd.to_datetime(base_enfant["date_naissance"], errors="coerce").dt.date

                resultats = []
                for _, row in base_actif.head(10).iterrows():
                    p = Retraite(
                        matricule=row["matricule"],
                        date_naissance=row["date_naissance"],
                        statut=row["statut"],
                        base_conjoint_=base_conjoint,
                        base_enfant_=base_enfant
                    )
                    engagement = PBO_(p)
                    resultats.append(engagement)

                base_actif.loc[base_actif.head(10).index, "Engagement"] = resultats
                st.success("✅ Calcul terminé ! (aperçu sur 10 lignes)")
                st.dataframe(base_actif.head(10))

                csv = base_actif.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Télécharger les résultats en CSV", csv, "resultats_cm.csv", "text/csv")
