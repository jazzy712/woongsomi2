from django.shortcuts                   import render, redirect, get_object_or_404
from django.views.decorators.http       import require_http_methods, require_POST
from django.contrib.auth.decorators     import login_required
from django.db.models                   import Count, Q
from django.http                        import JsonResponse
from django.core.paginator              import Paginator

from .models    import Board, Comment
from .forms     import BoardForm, CommentForm
from mbti.models import PersonalityType


@require_http_methods(["GET"])
def index(request):
    qs = Board.objects.all().order_by('-created_at')

    # 검색
    q = request.GET.get('q','').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(author__username__icontains=q)
        )

    # 페이징: 페이지당 10개
    paginator   = Paginator(qs, 10)
    page_number = request.GET.get('page')
    boards      = paginator.get_page(page_number)

    # 인기글: 조회수 상위 5개 (예시로 num_comments도 붙여봤습니다)
    popular_boards = Board.objects.annotate(
        num_comments=Count('comments')
    ).order_by('-view_count')[:5]

    mbti_types = PersonalityType.objects.all()

    return render(request, 'boards/index.html', {
        'boards':         boards,           # Page 객체
        'popular_boards': popular_boards,
        'mbti_types':     mbti_types,
        'q':              q,
    })

@require_http_methods(["GET", "POST"])
def detail(request, pk):
    board = get_object_or_404(Board, pk=pk)

    # 조회수 카운트 (자기 글 제외)
    if request.method == 'GET' and request.user.is_authenticated and request.user != board.author:
        board.view_count += 1
        board.save(update_fields=['view_count'])

    # 게시글 삭제 처리
    if request.method == 'POST' and request.user == board.author:
        board.delete()
        return redirect('boards:index')

    comments = board.comments.filter(parent_comment__isnull=True)
    comment_form = CommentForm()
    similar_boards = []
    if board.related_mbti_type:
        similar_boards = Board.objects.filter(
            related_mbti_type=board.related_mbti_type
        ).exclude(pk=board.pk)[:3]

    return render(request, 'boards/detail.html', {
        'board': board,
        'comments': comments,
        'comment_form': comment_form,
        'similar_boards': similar_boards,
    })


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            b = form.save(commit=False)
            b.author = request.user
            b.save()
            return redirect('boards:detail', b.pk)
    else:
        initial = {}
        if hasattr(request.user, 'mbti_type') and request.user.mbti_type:
            initial['related_mbti_type'] = request.user.mbti_type
        form = BoardForm(initial=initial)

    return render(request, 'boards/form.html', {
        'form': form,
        'mode': 'create'
    })


@login_required
@require_http_methods(["GET", "POST"])
def update(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if request.user != board.author:
        return redirect('boards:detail', pk)

    if request.method == 'POST':
        form = BoardForm(request.POST, instance=board)
        if form.is_valid():
            form.save()
            return redirect('boards:detail', pk)
    else:
        form = BoardForm(instance=board)

    return render(request, 'boards/form.html', {
        'form': form,
        'mode': 'update',
        'board': board,
    })


@login_required
@require_POST
def like_board(request, pk):
    board = get_object_or_404(Board, pk=pk)
    if request.user in board.likes.all():
        board.likes.remove(request.user)
        liked = False
    else:
        board.likes.add(request.user)
        liked = True
    return JsonResponse({
        'liked': liked,
        'count': board.likes.count()
    })


@login_required
@require_POST
def comment(request, board_pk):
    board = get_object_or_404(Board, pk=board_pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        c = form.save(commit=False)
        c.board = board
        c.author = request.user
        c.save()
    return redirect('boards:detail', board_pk)


@login_required
@require_POST
def like_comment(request, board_pk, comment_pk):
    comment = get_object_or_404(Comment, pk=comment_pk)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
        liked = False
    else:
        comment.likes.add(request.user)
        liked = True
    return JsonResponse({
        'liked': liked,
        'count': comment.likes.count()
    })

def mbti_type_filter(request, type_code):
    mbti_type = get_object_or_404(PersonalityType, type_code=type_code)
    boards = Board.objects.filter(
        related_mbti_type=mbti_type
    ).annotate(num_comments=Count('comments')).order_by('-created_at')
    return render(request, 'boards/index.html', {
        'boards': boards,
        'q': '',
        'popular_boards': [],     # 원하시는 대로
        'mbti_types': PersonalityType.objects.all(),
    })

def category_filter(request, category):
    boards = Board.objects.filter(
        category=category
    ).annotate(num_comments=Count('comments')).order_by('-created_at')
    return render(request, 'boards/index.html', {
        'boards': boards,
        'q': '',
        'popular_boards': [],
        'mbti_types': PersonalityType.objects.all(),
    })