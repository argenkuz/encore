from __future__ import annotations

from aiogram import Bot


class TelegramNotifier:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_car(
        self,
        telegram_id: int,
        car,
    ) -> None:
        """
        Отправляет найденный автомобиль пользователю Telegram.
        """

        title_parts = []

        if car.manufacturer:
            title_parts.append(
                car.manufacturer
            )

        if car.model:
            title_parts.append(
                car.model
            )

        if car.badge:
            title_parts.append(
                car.badge
            )

        title = " ".join(title_parts)

        if not title:
            title = "Новый автомобиль"


        # -------------------------------------------------
        # MESSAGE
        # -------------------------------------------------

        lines = [
            "🚗 <b>Найден новый автомобиль</b>",
            "",
            f"<b>{title}</b>",
        ]


        if car.year:
            lines.append(
                f"📅 Год: {car.year}"
            )


        if car.mileage is not None:
            lines.append(
                f"🛣 Пробег: "
                f"{car.mileage:,}".replace(",", " ")
                + " км"
            )


        if car.price is not None:
            lines.append(
                f"💰 Цена: "
                f"{car.price:,}".replace(",", " ")
                + " 만원"
            )


        if car.fuel_type:
            lines.append(
                f"⛽ Топливо: "
                f"{car.fuel_type}"
            )


        if car.region:
            lines.append(
                f"📍 Регион: "
                f"{car.region}"
            )


        if car.encar_url:
            lines.extend(
                [
                    "",
                    f'🔗 <a href="{car.encar_url}">'
                    "Открыть на Encar</a>",
                ]
            )


        message = "\n".join(lines)


        # -------------------------------------------------
        # SEND PHOTO
        # -------------------------------------------------

        if car.photo:
            try:
                await self.bot.send_photo(
                    chat_id=telegram_id,
                    photo=car.photo,
                    caption=message,
                    parse_mode="HTML",
                )

                return

            except Exception as error:
                print(
                    "Failed to send car photo:",
                    error,
                )


        # -------------------------------------------------
        # SEND TEXT
        # -------------------------------------------------

        await self.bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="HTML",
        )