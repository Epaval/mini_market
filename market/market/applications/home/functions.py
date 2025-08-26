# applications/home/functions.py

from django.db.models import Prefetch, F, FloatField, ExpressionWrapper
from django.utils import timezone
from datetime import datetime, date
from applications.venta.models import Sale, SaleDetail


def detalle_resumen_ventas(date_start, date_end):
    """
    Recupera ventas no anuladas en un rango de fechas,
    junto con el detalle de venta y el subtotal calculado.

    Acepta: str ('2025-08-25'), date o datetime.
    """
    # 1. Convertir strings a objetos date
    if isinstance(date_start, str):
        try:
            date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        except ValueError:
            return Sale.objects.none()

    if isinstance(date_end, str):
        try:
            date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        except ValueError:
            return Sale.objects.none()

    # 2. Validar que sean objetos date
    if not isinstance(date_start, date) or not isinstance(date_end, date):
        return Sale.objects.none()

    # 3. Convertir a datetime "aware" (con zona horaria)
    # Inicio del día de date_start
    if isinstance(date_start, date) and not isinstance(date_start, datetime):
        datetime_start = timezone.make_aware(
            datetime.combine(date_start, datetime.min.time())
        )
    else:
        datetime_start = date_start

    # Final del día de date_end
    if isinstance(date_end, date) and not isinstance(date_end, datetime):
        datetime_end = timezone.make_aware(
            datetime.combine(date_end, datetime.max.time())
        )
    else:
        datetime_end = date_end

    # 4. Validar que las fechas no sean "naive" si son datetime
    if timezone.is_naive(datetime_start) or timezone.is_naive(datetime_end):
        # Si son naive, conviértelas a "aware"
        if timezone.is_naive(datetime_start):
            datetime_start = timezone.make_aware(datetime_start)
        if timezone.is_naive(datetime_end):
            datetime_end = timezone.make_aware(datetime_end)

    # 5. Obtener ventas en rango de fechas
    ventas = Sale.objects.ventas_en_fechas(datetime_start, datetime_end)

    # 6. Prefetch del detalle con subtotal
    consulta = ventas.prefetch_related(
        Prefetch(
            'detail_sale',
            queryset=SaleDetail.objects.filter(sale__in=ventas).annotate(
                subtotal=ExpressionWrapper(
                    F('price_sale') * F('count'),
                    output_field=FloatField()
                )
            )
        )
    )

    return consulta