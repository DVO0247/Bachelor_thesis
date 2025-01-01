from .models import UserProject

def user_projects(request):
    """
    Přidá seznam projektů pro aktuálně přihlášeného uživatele do kontextu všech views.
    """
    if request.user.is_authenticated:
        # Získání všech projektů, kde je uživatel členem
        projects = UserProject.objects.filter(user=request.user).select_related('project')
        return {
            'user_projects': [user_project.project for user_project in projects],
        }
    return {'user_projects': []}
