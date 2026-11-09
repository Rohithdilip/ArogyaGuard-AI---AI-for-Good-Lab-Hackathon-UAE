"""Approved official-source manifest.

The archive contains *no* official PDFs. A user deliberately downloads/indexes them
from NHM; attribution, programme scope, local eligibility need verification.
"""
SOURCES = [
    {
      'id':'asha6','title':'ASHA Module 6 — Simple Skills that Save Lives',
      'kind':'pdf','category':'guidance',
      'url':'https://nhm.gov.in/images/pdf/communitisation/asha/book-no-6.pdf',
      'scope':'India · ASHA training',
      'summary':'ASHA community health guidance covers antenatal counselling, maternal danger signs and facilitating prompt facility referral. Severe headache with blurred vision, bleeding and convulsions are examples needing urgent clinical attention. ASHA workers support linkage to trained providers; this is not an AI diagnosis.'
    },
    {
      'id':'asha_induction','title':'NHM ASHA Induction Training Module',
      'kind':'pdf','category':'guidance',
      'url':'https://nhm.gov.in/images/pdf/communitisation/asha/ASHA_Induction_Module_English.pdf',
      'scope':'India · ASHA worker training',
      'summary':'An ASHA worker helps families reach maternal and child health services, supports community awareness and pregnancy-related counselling, and links women to appropriate public-sector healthcare facilities. This is a training reference, not an individual treatment protocol.'
    },
    {
      'id':'jssk','title':'NHM — JSSK programme and entitlements',
      'kind':'pdf','category':'benefits',
      'url':'https://nhm.gov.in/images/pdf/programmes/guidelines-for-jssk.pdf',
      'scope':'India · public-sector maternal services; verify implementation',
      'summary':'Janani Shishu Suraksha Karyakram (JSSK) describes free and cashless maternity entitlements at government health institutions, including delivery, drugs, consumables, diagnostics, blood, diet, transport from home, facility-to-facility referrals and drop-back under programme conditions. Confirm current state delivery, service coverage, eligibility and transport availability locally.'
    },
    {
      'id':'pmsma','title':'PMSMA Operational Framework',
      'kind':'pdf','category':'followup',
      'url':'https://nhm.gov.in/images/pdf/programmes/maternal-health/guidelines/PMSMA_Operational_Framework.pdf',
      'scope':'India · ANC programme',
      'summary':'Pradhan Mantri Surakshit Matritva Abhiyan provides fixed-day antenatal services, including screening for high-risk pregnancy, clinical evaluation and appropriate follow-up or referral. The programme is associated with the 9th day of each month; clinicians decide patient-specific care.'
    },
    {
      'id':'extended_pmsma','title':'NHM — Extended PMSMA High-Risk Pregnancy Tracking',
      'kind':'pdf','category':'followup',
      'url':'https://nhm.gov.in/New_Update-2022-23/MH/GUIDELINES-%20MH/Guidance_Note-Extended_PMSMA_for_tracking_HRPs.pdf',
      'scope':'Initial phase: 17 named states, *not* Telangana; verify later expansion',
      'summary':'Extended PMSMA guidance discusses line-listing high-risk pregnancy, ASHA/ANM follow-up, doctor-led antenatal visits and linkages to referral units. Its first-phase incentive rollout names 17 states and does not include Telangana. Never promise a Telangana-specific Extended PMSMA incentive based on this original guidance alone.'
    },
    {
      'id':'suman','title':'NHM — SUMAN Guidelines (2020)',
      'kind':'pdf','category':'governance',
      'url':'https://nhm.gov.in/New_Updates_2018/NHM_Components/RMNCHA/MH/Guidelines/SUMAN%20Guideline%202020%20Web%20Version.pdf',
      'scope':'India · facility maternity care; verify current local practices',
      'summary':'Surakshit Matritva Aashwasan (SUMAN) provides a framework for assured, respectful and dignified maternity services, quality of care, accountability and grievance mechanisms. The frontline worker should validate local service arrangements and escalate unresolved issues to an authorized provider.'
    },
]
CATALOG = {d['id']: d for d in SOURCES}

LANGUAGES = {'en':'English', 'hi':'हिन्दी', 'te':'తెలుగు', 'kn':'ಕನ್ನಡ'}
AGENTS = ('guidance', 'benefits', 'followup')
AGENT_LABELS = {'guidance':'Maternal Guidance & Referral', 'benefits':'Benefits & Entitlements', 'followup':'Follow-up & Care Continuity', 'governance':'Governance & Evidence'}
AGENT_CATEGORIES = {'guidance':('guidance','followup'), 'benefits':('benefits',), 'followup':('followup', 'guidance')}
