from .models import UserProject

def user_projects(request):
    """
    Adds the list of projects for the currently logged in user to the context of all views.
    """
    if request.user.is_authenticated:
        # Get all projects where the user is a member
        projects = UserProject.objects.filter(user=request.user).select_related('project')
        return {
            'user_projects': projects,
        }
    return {'user_projects': []}
