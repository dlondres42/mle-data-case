import datetime

EXTRACTION_PROMPT_TEMPLATE = """\
Você é um extrator de informações de incidentes. Analise a descrição abaixo e \
responda APENAS com um objeto JSON válido, sem nenhum texto adicional, contendo \
exatamente estas chaves:

- "data_ocorrencia": data e hora do incidente, ou null se ausente
- "local": local do incidente, ou null se ausente
- "tipo_incidente": tipo ou categoria do incidente, ou null se ausente
- "impacto": descrição breve do impacto gerado, ou null se ausente

Hoje é {today}. Converta datas relativas (como "ontem" ou "semana passada") \
para datas absolutas no formato "YYYY-MM-DD HH:MM".

Descrição do incidente:
{text}
"""


def build_extraction_prompt(text: str, today: datetime.date | None = None) -> str:
    today = today or datetime.date.today()
    return EXTRACTION_PROMPT_TEMPLATE.format(text=text, today=today.isoformat())
