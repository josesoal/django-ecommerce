from ctypes import addressof
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

from base.models import Product, Order, OrderItem, ShippingAddress
from base.serializers import ProductSerializer, OrderSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def addOrderItems(request):
    user = request.user
    data = request.data

    orderItems = data['orderItems']
    if orderItems and len(orderItems) == 0:
        message = {'detail': 'No order items'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    else:
        # (1) create order
        order = Order.objects.create(
            user = user,
            paymentMethod = data['paymentMethod'],
            taxPrice = data['taxPrice'],
            shippingPrice = data['shippingPrice'],
            totalPrice = data['totalPrice']
        )

        # (2) create shipping address
        shipping = ShippingAddress.objects.create(
            order = order,
            address  = data['shippingAddress']['address'],
            city = data['shippingAddress']['city'],
            postalCode = data['shippingAddress']['postalCode'],
            country = data['shippingAddress']['country']
        )

        # (3) create order items and set order-relationship (foreing key)
        for i in orderItems:
            product = Product.objects.get( _id=i['product'] )

            orderItem = OrderItem.objects.create(
                product = product,
                order = order,
                name = product.name,
                qty = i['qty'],
                price = i['price'],
                image = product.image.url
            ) 
        
            # (4) update stock
            product.countInStock -= orderItem.qty  
            product.save() 
     
        serializer = OrderSerializer(order, many=False)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getOrderById(request, pk):
    user = request.user
    order = Order.objects.get( _id=pk )

    try:
        if user.is_staff or order.user == user:
            serializer = OrderSerializer( order, many=False )
            return Response( serializer.data )
        else:
            message = {'detail': 'Not authorized to view this order'}
            return Response( message, status=status.HTTP_400_BAD_REQUEST )
    except:
        message = {'detail': 'Order does not exist'}
        return Response( message, status=status.HTTP_400_BAD_REQUEST )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getMyOrders(request):
    user = request.user
    orders = user.order_set.all()
    serializer = OrderSerializer( orders, many=True )
    return Response( serializer.data )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def updateOrderToPaid(request, pk):
    user = request.user
    order = Order.objects.get( _id=pk )

    if order.user == user:
        order.isPaid = True
        order.paidAt = datetime.now()
        order.save()
        return Response( 'Order was paid' )
    else:
        message = {'detail': 'Not authorized to pay this order'}
        return Response( message, status=status.HTTP_400_BAD_REQUEST )
    