from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ..models import Product, Review
from ..serializers import ProductSerializer

# Create your views here.


@api_view(['GET'])
def getProducts(request):
    keyword = request.query_params.get('keyword')
    page = request.query_params.get('page')

    if keyword == None:
        keyword = ''

    products = Product.objects.filter(
        name__icontains=keyword).order_by('createdAt')
    paginator = Paginator(products, 5) # each page with 5 items

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
        page = 1
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
        page = paginator.num_pages

    page = int(page)
    serializer = ProductSerializer(products, many=True)
    return Response({
        'products': serializer.data, 
        'page': page, 
        'pages': paginator.num_pages
    })


@api_view(['GET'])
def getTopProducts(request):
    products = Product.objects.all().order_by('-rating')[0:5]
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def getProduct(request, pk):
    product = Product.objects.get(_id=pk)
    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def createProduct(request):
    user = request.user

    product = Product.objects.create(
        user=user,
        name='Sample Name',
        price=0,
        brand='Sample Brand',
        countInStock=0,
        category='Sample Category',
        description=''
    )

    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAdminUser])
def updateProduct(request, pk):
    data = request.data
    product = Product.objects.get(_id=pk)

    product.name = data['name']
    product.price = data['price']
    product.brand = data['brand']
    product.countInStock = data['countInStock']
    product.category = data['category']
    product.description = data['description']
    product.save()

    serializer = ProductSerializer(product, many=False)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def deleteProduct(request, pk):
    product = Product.objects.get(_id=pk)
    product.delete()
    return Response('Product was deleted')


@api_view(['POST'])
def uploadImage(request):
    data = request.data

    product_id = data['product_id']
    product = Product.objects.get(_id=product_id)

    product.image = request.FILES.get('image')
    product.save()

    return Response('Image was uploaded')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createProductReview(request, pk):
    data = request.data
    user = request.user
    product = Product.objects.get(_id=pk)

    # 1 - review already exists
    alreadyExists = product.review_set.filter(user=user).exists()

    if alreadyExists:
        message = {'detail': 'Product already reviewed'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    # 2 - no rating or 0
    if data['rating'] == 0:
        message = {'detail': 'Please select a rating'}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)

    # 3 - create review
    else: 
        review = Review.objects.create(
            product = product,
            user = user,
            name = user.first_name,
            rating = data['rating'],
            comment = data['comment']
        )
        
        # update number of reviews of product
        reviews = product.review_set.all()
        product.numReviews = len(reviews)

        # update rating of product
        total = 0
        for rev in reviews:
            total += rev.rating
        
        product.rating = total / len(reviews)
        product.save()
        
        return Response('Review added')
