from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse

from .models import Board, Comment
from .forms import BoardForm, CommentForm
from mbti.models import PersonalityType

@require_http_methods(["GET"])
def index(request):
    boards = Board.objects.annotate(comment_count=Count('comments')).order_by('-created_at')
    
    # 검색 기능
    query = request.GET.get('q')
    if query:
        boards = boards.filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        )
    
    # 인기글(조회수 상위) 5개 조회
    popular_boards = Board.objects.annotate(comment_count=Count('comments')).order_by('-view_count')[:5]
    
    # MBTI 유형 정보
    mbti_types = PersonalityType.objects.all()
    
    context = {
        'boards': boards,
        'popular_boards': popular_boards,
        'mbti_types': mbti_types,
    }
    return render(request, 'boards/index.html', context)

@require_http_methods(["GET", "POST"])
def detail(request, pk):
    board = get_object_or_404(Board, pk=pk)
    
    # 조회수 증가
    if request.user.is_authenticated and request.user != board.author:
        board.view_count += 1
        board.save()
    
    if request.method == 'POST':
        # 게시글 삭제 요청
        if request.user == board.author:
            board.delete()
            return redirect('boards:index')
        return redirect('boards:detail', pk)

    comments = board.comments.filter(parent_comment__isnull=True)  # 최상위 댓글만 조회
    comment_form = CommentForm()
    
    # 비슷한 MBTI 유형의 추천 게시글
    similar_boards = []
    if board.related_mbti_type:
        similar_boards = Board.objects.filter(
            related_mbti_type=board.related_mbti_type
        ).exclude(
            pk=board.pk
        ).order_by('-created_at')[:3]

    context = {
        'board': board,
        'comments': comments,
        'comment_form': comment_form,
        'similar_boards': similar_boards,
    }
    return render(request, 'boards/detail.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def update(request, pk):
    board = get_object_or_404(Board, pk=pk)
    
    # 작성자만 수정 가능
    if request.user != board.author:
        return redirect('boards:detail', board.pk)

    if request.method == 'POST':
        form = BoardForm(request.POST, instance=board)
        if form.is_valid():
            form.save()
            return redirect('boards:detail', board.pk)
    else:
        form = BoardForm(instance=board)
    
    context = {
        'board': board,
        'form': form,
    }
    return render(request, 'boards/update.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.author = request.user
            board.save()
            return redirect('boards:detail', board.pk)
    else:
        # MBTI 유형에 맞는 카테고리 자동 선택
        initial_data = {}
        if request.user.mbti_type:
            initial_data['related_mbti_type'] = request.user.mbti_type
        
        form = BoardForm(initial=initial_data)
    
    context = {
        'form': form,
    }
    return render(request, 'boards/create.html', context)

@login_required
@require_POST
def like_board(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if board.likes.filter(pk=request.user.pk).exists():
        board.likes.remove(request.user)
        liked = False
    else:
        board.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likeCount': board.likes.count(),
    })

def category_filter(request, category):
    boards = Board.objects.filter(category=category).annotate(comment_count=Count('comments')).order_by('-created_at')
    
    context = {
        'boards': boards,
        'category': category,
    }
    return render(request, 'boards/category_filter.html', context)

def mbti_type_filter(request, type_code):
    mbti_type = get_object_or_404(PersonalityType, type_code=type_code)
    boards = Board.objects.filter(related_mbti_type=mbti_type).annotate(comment_count=Count('comments')).order_by('-created_at')
    
    context = {
        'boards': boards,
        'mbti_type': mbti_type,
    }
    return render(request, 'boards/mbti_type_filter.html', context)

def user_filter(request, user_pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = get_object_or_404(User, pk=user_pk)
    boards = Board.objects.filter(author=user).annotate(comment_count=Count('comments')).order_by('-created_at')
    
    context = {
        'boards': boards,
        'filter_user': user,
    }
    return render(request, 'boards/user_filter.html', context)

@login_required
@require_POST
def comment(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.board = board
        comment.author = request.user
        comment.save()
    return redirect('boards:detail', board.pk)

@login_required
@require_POST
def create_reply(request, comment_pk):
    parent_comment = get_object_or_404(Comment, id=comment_pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        reply_comment = form.save(commit=False)
        reply_comment.board = parent_comment.board
        reply_comment.author = request.user
        reply_comment.parent_comment = parent_comment
        reply_comment.save()
    return redirect("boards:detail", parent_comment.board.id)

@require_POST
def comment_detail(request, board_pk, comment_pk):
    comment = get_object_or_404(Comment, pk=comment_pk)
    
    # 작성자만 삭제 가능
    if request.method == 'POST' and request.user == comment.author:
        comment.delete()
    
    return redirect('boards:detail', board_pk)

@login_required
@require_POST
def like_comment(request, board_pk, comment_pk):
    comment = get_object_or_404(Comment, pk=comment_pk)
    if comment.likes.filter(pk=request.user.pk).exists():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likeCount': comment.likes.count(),
    })
