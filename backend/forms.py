from django import forms

INPUT = ("mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm "
         "outline-none focus:border-brand focus:ring-2 focus:ring-brand/20")


class SettingsForm(forms.Form):
    ollama_base_url = forms.URLField(label="Адрес Ollama", help_text="Обычно http://localhost:11434")
    ollama_model = forms.CharField(label="Модель", max_length=100, help_text="Должна быть загружена в Ollama")
    ollama_timeout = forms.IntegerField(label="Таймаут, секунд", min_value=5, max_value=600,
                                        help_text="Сколько ждать ответ на один запрос")
    ollama_temperature = forms.FloatField(label="Температура", min_value=0, max_value=1,
                                          widget=forms.NumberInput(attrs={"step": "0.1"}),
                                          help_text="0 даёт воспроизводимые результаты")
    use_llm = forms.BooleanField(label="Использовать LLM", required=False)
    batch_max_rows = forms.IntegerField(label="Максимум строк в CSV", min_value=1, max_value=100000,
                                        help_text="Ограничение для массовой обработки")
    confidence_high = forms.FloatField(label="Порог принятия", min_value=0, max_value=1,
                                       widget=forms.NumberInput(attrs={"step": "0.01"}))
    confidence_low = forms.FloatField(label="Порог неизвестного", min_value=0, max_value=1,
                                      widget=forms.NumberInput(attrs={"step": "0.01"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["class"] = "peer sr-only" if name == "use_llm" else INPUT
        self.fields["ollama_model"].widget.attrs["list"] = "models-list"

    def clean_ollama_base_url(self):
        return self.cleaned_data["ollama_base_url"].rstrip("/")

    def clean(self):
        data = super().clean()
        low, high = data.get("confidence_low"), data.get("confidence_high")
        if low is not None and high is not None and low >= high:
            self.add_error("confidence_low", "Порог неизвестного должен быть меньше порога принятия")
        return data