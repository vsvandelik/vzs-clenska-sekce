.. _forms:

***************************************
Formuláře
***************************************
Django obsahuje celou řadu vzorů a komponent pro práci s formuláři. Tyto komponenty se nacházejí v knihovně ``django.forms`` a jsou v maximální možné míře využívány. Základním stavebním prvkem jsou třídy ``Form`` a  ``ModelForm``, které definují políčka formuláře. :term:`IS` používá zejména třídu ``ModelForm``.

Třída ``ModelForm`` umožňuje na rozdíl od třídy ``Form`` vytvořit formulář mapující se na konkrétní model. Výhodou tohoto přístupu na rozdíl od ručního vytváření formulářů je automatická základní server-side validace dat. Pokud je vyžadována pokročilá validace, je možné ji implementovat přetížením metody ``clean``. V případě použití třídy ``ModelForm`` se dokonce sama namapují políčka formuláře na model, který je možné před uložením upravit přetížením funkce ``save``.

Pro účely zlepšení UX byla pro všechny formuláře implementována i validace na straně klienta pomocí Javascriptu. V případech, kdy to bylo výhodné z hlediska přehlednosti a množství kódu, bylo využito jQuery.

Formuláře se renderují v jednotném Bootstrap stylu, který má na starosti rozšíření :ref:`django-crispy-forms` s balíčkem šablon :ref:`crispy-bootstrap4`. V šabloně pro Jinju se celý formulář renderuje příkazem ``{% crispy form %}``. Případně je možné renderovat formulář po políčkách s použitím template filtru (viz :doc:`./template-filters`).

Příklad renderování formuláře po políčkách:

.. code-block:: console

    <div class="card-body">
        {{ form.name|as_crispy_field }}
        {{ form.category|as_crispy_field }}
        {{ form.description|as_crispy_field }}
        {{ form.capacity|as_crispy_field }}
        {{ form.location|as_crispy_field }}
        {{ form.participants_enroll_state|as_crispy_field }}
    </div>

Příklad formuláře:

.. code-block:: python

    class TrainingEnrollMyselfParticipantOccurrenceForm(
        OccurrenceFormMixin, ActivePersonFormMixin, ModelForm
    ):
        class Meta:
            model = TrainingParticipantAttendance
            fields = []

        def clean(self):
            cleaned_data = super().clean()
            if not self.occurrence.can_participant_enroll(self.person):
                self.add_error(
                    None, "Nemáte oprávnění k jednorázovému přihlášení na tento trénink"
                )
            return cleaned_data

        def save(self, commit=True):
            instance = super().save(False)
            instance.person = self.person
            instance.occurrence = self.occurrence
            instance.state = TrainingAttendance.PRESENT
            self._one_time_attendance_created(instance)
            if commit:
                instance.save()
            return instance

        def _one_time_attendance_created(self, attendance):
            send_notification_email(
                _("Jednorázová účast na tréninku"),
                _(
                    f"Potvrzujeme vaši přihlášku jako jednorázový účastník dne {date_pretty(attendance.occurrence.datetime_start)} tréninku {attendance.occurrence.event}"
                ),
                [attendance.person],
            )

Tento formulář byl záměrně vybrán pro účely demonstrace použití formulářů, protože je jednoduchý a implementuje obě funkce ``clean`` i ``save``.

Formulář je využíván při přihlášení náhradní účasti na trénink. Formulář vyžaduje osobu (``person``), den tréninku (``occurrence``). Osoba je aktuálně přihlášená ze session, formulář ji získá v ``self.person`` při použití ``ActivePersonFormMixin``. Den tréninku víme z URL cesty, formulář ho získá v ``self.occurrence`` při použití ``OccurrenceFormMixin``.

Třída ``Meta`` definuje jakému modelu odpovídá formulář a jaká políčka z modelu využívá. Metoda ``clean`` implementuje jednu kontrolu, kdy se ověřuje zda osoba má právo se přihlásit na trénink. V metodě ``save`` se upraví model, přiřadí se osoba a trénink a také se nastaví předpokládaná přítomnost účastníka. Před uložením se ještě odešle účastníkovi e-mail potvrzující jeho přihlášku.
