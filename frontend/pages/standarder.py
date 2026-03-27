import streamlit as st

def main():
    st.title("📚 Standarder")
    st.markdown("---")
    st.info(
        "Her finner du relevante tekniske standarder og normer for geoteknikk og peling.\n\n_Funksjonalitet er under utvikling._"
    )
    st.markdown("#### Planlagte standarder")
    st.markdown("""
    - NS-EN 1997 (Eurocode 7) — Geoteknisk prosjektering  
    - NS-EN 12699 — Utførelse av spesielle geotekniske arbeider  
    - NS-EN 14199 — Mikropeler  
    - NGF-veiledninger  
    """)

if __name__ == "__main__":
    main()
