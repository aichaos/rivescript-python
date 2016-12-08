# RiveScript-Python
#
# This code is released under the MIT License.
# See the "LICENSE" file for more information.
#
# https://www.rivescript.com/

def get_topic_triggers(rs, topic, thats, depth=0, inheritance=0, inherited=False):
    """Recursively scan a topic and return a list of all triggers.

    Arguments:
        rs (RiveScript): A reference to the parent RiveScript instance.
        topic (str): The original topic name.
        thats (bool): Are we getting triggers for 'previous' replies?
        depth (int): Recursion step counter.
        inheritance (int): The inheritance level counter, for topics that
            inherit other topics.
        inherited (bool): Whether the current topic is inherited by others.

    Returns:
        []str: List of all triggers found.
    """

    # Break if we're in too deep.
    if depth > rs._depth:
        rs._warn("Deep recursion while scanning topic inheritance")

    # Keep in mind here that there is a difference between 'includes' and
    # 'inherits' -- topics that inherit other topics are able to OVERRIDE
    # triggers that appear in the inherited topic. This means that if the top
    # topic has a trigger of simply '*', then NO triggers are capable of
    # matching in ANY inherited topic, because even though * has the lowest
    # priority, it has an automatic priority over all inherited topics.
    #
    # The getTopicTriggers method takes this into account. All topics that
    # inherit other topics will have their triggers prefixed with a fictional
    # {inherits} tag, which would start at {inherits=0} and increment if this
    # topic has other inheriting topics. So we can use this tag to make sure
    # topics that inherit things will have their triggers always be on top of
    # the stack, from inherits=0 to inherits=n.

    # Important info about the depth vs inheritance params to this function:
    # depth increments by 1 each time this function recursively calls itrs.
    # inheritance increments by 1 only when this topic inherits another
    # topic.
    #
    # This way, '> topic alpha includes beta inherits gamma' will have this
    # effect:
    #  alpha and beta's triggers are combined together into one matching
    #  pool, and then those triggers have higher matching priority than
    #  gamma's.
    #
    # The inherited option is True if this is a recursive call, from a topic
    # that inherits other topics. This forces the {inherits} tag to be added
    # to the triggers. This only applies when the top topic 'includes'
    # another topic.
    rs._say("\tCollecting trigger list for topic " + topic + "(depth="
        + str(depth) + "; inheritance=" + str(inheritance) + "; "
        + "inherited=" + str(inherited) + ")")

    # topic:   the name of the topic
    # depth:   starts at 0 and ++'s with each recursion

    # Topic doesn't exist?
    if not topic in rs._topics:
        rs._warn("Inherited or included topic {} doesn't exist or has no triggers".format(
            topic
        ))
        return []

    # Collect an array of triggers to return.
    triggers = []

    # Get those that exist in this topic directly.
    inThisTopic = []
    if not thats:
        # The non-that structure is {topic}->[array of triggers]
        if topic in rs._topics:
            for trigger in rs._topics[topic]:
                inThisTopic.append([ trigger["trigger"], trigger ])
    else:
        # The 'that' structure is: {topic}->{cur trig}->{prev trig}->{trig info}
        if topic in rs._thats.keys():
            for curtrig in rs._thats[topic].keys():
                for previous, pointer in rs._thats[topic][curtrig].items():
                    inThisTopic.append([ pointer["trigger"], pointer ])

    # Does this topic include others?
    if topic in rs._includes:
        # Check every included topic.
        for includes in rs._includes[topic]:
            rs._say("\t\tTopic " + topic + " includes " + includes)
            triggers.extend(get_topic_triggers(rs, includes, thats, (depth + 1), inheritance, True))

    # Does this topic inherit others?
    if topic in rs._lineage:
        # Check every inherited topic.
        for inherits in rs._lineage[topic]:
            rs._say("\t\tTopic " + topic + " inherits " + inherits)
            triggers.extend(get_topic_triggers(rs, inherits, thats, (depth + 1), (inheritance + 1), False))

    # Collect the triggers for *this* topic. If this topic inherits any
    # other topics, it means that this topic's triggers have higher
    # priority than those in any inherited topics. Enforce this with an
    # {inherits} tag.
    if topic in rs._lineage or inherited:
        for trigger in inThisTopic:
            rs._say("\t\tPrefixing trigger with {inherits=" + str(inheritance) + "}" + trigger[0])
            triggers.append(["{inherits=" + str(inheritance) + "}" + trigger[0], trigger[1]])
    else:
        triggers.extend(inThisTopic)

    return triggers

def get_topic_tree(rs, topic, depth=0):
    """Given one topic, get the list of all included/inherited topics.

    :param str topic: The topic to start the search at.
    :param int depth: The recursion depth counter.

    :return []str: Array of topics.
    """

    # Break if we're in too deep.
    if depth > rs._depth:
        rs._warn("Deep recursion while scanning topic trees!")
        return []

    # Collect an array of all topics.
    topics = [topic]

    # Does this topic include others?
    if topic in rs._includes:
        # Try each of these.
        for includes in sorted(rs._includes[topic]):
            topics.extend(get_topic_tree(rs, includes, depth + 1))

    # Does this topic inherit others?
    if topic in rs._lineage:
        # Try each of these.
        for inherits in sorted(rs._lineage[topic]):
            topics.extend(get_topic_tree(rs, inherits, depth + 1))

    return topics
