import streamlit as st

def main():
    st.title("🤖 GeoGPT")
    st.markdown("---")
    st.info(
        """**GeoGPT** er en AI-assistent spesialisert for geoteknikk.\n\n
Her vil du kunne stille spørsmål om geotekniske standarder, tolke grunnundersøkelser, og få hjelp med beregninger.\n\n
_Funksjonalitet er under utvikling._"""
    )
    st.markdown("#### Planlagte funksjoner")
    st.markdown("""
    - 💬 Chat-grensesnitt for geotekniske spørsmål  
    - 📄 Opplasting og analyse av rapporter  
    - 🔗 Kobling mot prosjektdata i RamGAP  
    - 📚 Søk i standarder og normer  
    """)

if __name__ == "__main__":
    main()
