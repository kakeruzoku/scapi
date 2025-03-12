# Special Thanks: Timmccool / https://github.com/TimMcCool/scratchattach

#███████╗ ██████╗ █████╗ ██████╗ ██╗
#██╔════╝██╔════╝██╔══██╗██╔══██╗██║
#███████╗██║     ███████║██████╔╝██║
#╚════██║██║     ██╔══██║██╔═══╝ ██║
#███████║╚██████╗██║  ██║██║     ██║
#╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝
# Created by kakeruzoku [kakeruzoku@gmail.com]
# pip install scapi / https://github.com/kakeruzoku/scapi 

from .others.common import (
    create_ClientSession,
    create_custom_ClientSession,
    Response,
    ClientSession,
    api_iterative as _api_iterative,
    split_int,
    split,
    to_dt,
    empty_project_json,
    BIG,
    __version__
)
from .others import error as exception
del exception.TYPE_CHECKING
from .others.other_api import (
    check_username,
    check_password,
    total_site_stats,
    monthly_site_traffic,
    monthly_activity,
    translation,
    tts
)
from .sites.base import (
    _BaseSiteAPI,
    get_list_data,
    get_page_list_data
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
    search_projects,
    RemixTree,
    get_remixtree
)
from .sites.session import (
    SessionStatus,
    Session,
    session_login,
    login,
    send_password_reset_email
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
    create_Partial_User,
    is_allowed_username
)
from .sites.activity import (
    Activity,
    ActivityType,
    CloudActivity
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
from .sites.mainpage import (
    ScratchNews,
    get_scratchnews,
    community_featured,
    community_featured_response,
)


from .cloud.cloud import (
    _BaseCloud,
    TurboWarpCloud,
    get_tw_cloud
)
from .cloud.cloud_event import (
    CloudEvent
)
from .cloud.server import (
    CloudServerConnection,
    CloudServerPolicy,
    CloudServer
)

from .event._base import _BaseEvent
from .event.comment import CommentEvent
from .event.message import MessageEvent,SessionMessageEvent
