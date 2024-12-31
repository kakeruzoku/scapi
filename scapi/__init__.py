# Special Thanks: Timmccool / https://github.com/TimMcCool/scratchattach

#███████╗ ██████╗ █████╗ ██████╗ ██╗
#██╔════╝██╔════╝██╔══██╗██╔══██╗██║
#███████╗██║     ███████║██████╔╝██║
#╚════██║██║     ██╔══██║██╔═══╝ ██║
#███████║╚██████╗██║  ██║██║     ██║
#╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝
# Created by kakeruzoku [kakeruzoku@gmail.com]
# pip install scapi / https://github.com/kakeruzoku/scapi 

__version__ = "0.3.1"

from .others.common import (
    create_ClientSession,
    Response,
    ClientSession,
    api_iterative as _api_iterative,
    split_int,
    split,
    to_dt,
    empty_project_json,
    BIG
)
from .others import error as exception
del exception.TYPE_CHECKING
from .others.other_api import (
    get_csrf_token_sync
)
from .sites.base import (
    _BaseSiteAPI,
)
from .sites.comment import (
    CommentData,
    Comment,
    UserComment
)
from .sites.project import (
    Project,
    get_project,
    create_Partial_Project,
    explore_projects,
    search_projects
)
from .sites.session import (
    SessionStatus,
    Session,
    session_login,
    login
)
from .sites.studio import (
    Studio,
    get_studio,
    create_Partial_Studio,
    explore_studios,
    search_studios
)
from .sites.user import (
    User,
    get_user,
    create_Partial_User
)
from .sites.activity import (
    Activity,
    ActivityType
)
from .sites.forum import (
    ForumTopic,
    ForumCategoryType,
    ForumPost,
    ForumStatus,
    get_post,
    get_topic,
    get_topic_list,
    create_Partial_ForumTopic,
    create_Partial_ForumPost,
)
from .sites.classroom import (
    Classroom,
    get_classroom,
    get_classroom_by_token,
    create_Partial_classroom
)
