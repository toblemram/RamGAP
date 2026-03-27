import streamlit as st

def main():
    st.title("🎓 Opplæring")
    st.markdown("---")
    st.info(
        "Kurs og opplæringsmateriell for bruk av RamGAP.\n\n_Innhold er under utvikling._"
    )
    st.markdown("#### Planlagte moduler")
    st.markdown("""
    - 🟢 Kom i gang med RamGAP  
    - 🔧 Plaxis-automatisering trinn for trinn  
    - 🗺️ GeoTolk — tolking av sonderinger  
    - 🤖 Bruk av GeoGPT  
    """)

if __name__ == "__main__":
    main()
