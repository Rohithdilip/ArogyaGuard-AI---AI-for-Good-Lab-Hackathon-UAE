"""Independent *conservative* safety backstop; not a clinical triage classifier.

It does not attempt diagnosis. A lexical match is not evidence a condition exists;
negated/uncertain terms receive a confirmation notice. Clinicians own triage.
"""
import re

PHRASES = [
    r'severe headache', r'blurred vision', r'blurred eyesight', r'seeing spots',
    r'heavy bleeding', r'vaginal bleeding', r'bleeding', r'convulsions?',
    r'seizures?', r'fits', r'unconscious', r'difficulty breathing',
    r'తీవ్రమైన తలనొప్పి', r'చూపు మసక', r'రక్తస్రావ', r'మూర్ఛ',
    r'तेज सिरदर्द', r'धुंधला', r'रक्तस्राव', r'दौरे', r'बेहोश',
    r'ತೀವ್ರ ತಲೆನೋವು', r'ಮಸುಕಾದ ದೃಷ್ಟಿ', r'ರಕ್ತಸ್ರಾವ', r'ಸೆಳೆತ',
]
NEGATION_CUES = [r'\bno\b',r'\bnot\b',r'\bwithout\b',r'\bdenies\b',r'లేదు',r'नहीं',r'ಇಲ್ಲ']


def safety_screen(text: str) -> dict:
    low = text.lower()
    # Negation is checked *locally* around each matched term. For example,
    # 'no money and severe bleeding' remains an urgent warning, whereas
    # 'no severe headache' triggers a wording-confirmation notice.
    present=[]; uncertain=[]
    for pattern in PHRASES:
        for match in re.finditer(pattern,low,flags=re.I):
            prefix=low[max(0,match.start()-35):match.start()]
            # Look only at the last few words in the same clause; do not let
            # 'no transport' negate a later clinical danger-sign mention.
            prefix=re.split(r'[,.!?;]|\band\b|\bbut\b',prefix)[-1]
            tail=' '.join(prefix.split()[-4:])
            negated=any(re.search(n,tail,flags=re.I) for n in NEGATION_CUES)
            (uncertain if negated else present).append(pattern)
    return {'possible_danger':bool(present), 'uncertain_language':bool(uncertain),
            'matched_count':len(present)+len(uncertain)}


def notice(language: str, urgent: bool, uncertain: bool) -> str:
    if not urgent and not uncertain:
        return ''
    messages = {
      'en': ('Potential pregnancy danger signs were mentioned. Seek urgent assessment from a qualified healthcare professional; do not delay referral for this AI response.',
             'A danger-sign term may be negated or uncertain. Confirm the actual symptoms with the patient; if present, arrange urgent professional assessment.'),
      'hi': ('गर्भावस्था के संभावित खतरे के लक्षण बताए गए हैं। तुरंत योग्य स्वास्थ्यकर्मी से मूल्यांकन कराएँ; AI के उत्तर के लिए रेफरल में देरी न करें।',
             'खतरे के लक्षण का उल्लेख अस्पष्ट या नकारात्मक हो सकता है। लक्षण की पुष्टि करें; मौजूद होने पर तत्काल चिकित्सकीय मदद लें।'),
      'te': ('గర్భధారణలో ప్రమాద సూచనలు ప్రస్తావించబడ్డాయి. వెంటనే అర్హత కలిగిన ఆరోగ్య నిపుణుడి వద్ద పరీక్ష చేయించండి. AI సమాధానం కోసం రిఫరల్ ఆలస్యం చేయవద్దు.',
             'ప్రమాద సూచన లేదని లేదా స్పష్టంగా లేదని చెప్పి ఉండవచ్చు. లక్షణం ఉందో లేదో నిర్ధారించండి; ఉంటే వెంటనే వైద్య సహాయం పొందండి.'),
      'kn': ('ಗರ್ಭಾವಸ್ಥೆಯ ಅಪಾಯದ ಸೂಚನೆಗಳು ಉಲ್ಲೇಖವಾಗಿವೆ. ತಕ್ಷಣ ಅರ್ಹ ಆರೋಗ್ಯ ವೃತ್ತಿಪರರಿಂದ ಪರೀಕ್ಷೆ ಮಾಡಿಸಿ. AI ಉತ್ತರಕ್ಕಾಗಿ ರೆಫರಲ್ ವಿಳಂಬ ಮಾಡಬೇಡಿ.',
             'ಅಪಾಯದ ಲಕ್ಷಣದ ಉಲ್ಲೇಖ ಅಸ್ಪಷ್ಟವಾಗಿರಬಹುದು ಅಥವಾ ನಿರಾಕರಿಸಿರಬಹುದು. ಲಕ್ಷಣವನ್ನು ದೃಢಪಡಿಸಿ; ಇದ್ದರೆ ತಕ್ಷಣ ವೈದ್ಯಕೀಯ ನೆರವು ಪಡೆಯಿರಿ.')
    }
    a, b = messages.get(language, messages['en'])
    return a if urgent else b
