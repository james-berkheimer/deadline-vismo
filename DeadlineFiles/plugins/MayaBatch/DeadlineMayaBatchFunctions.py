import json

import maya.cmds
import maya.mel

def getCurrentRenderLayer():
    return maya.cmds.editRenderLayerGlobals( query=True, currentRenderLayer=True )

# A method mimicing the built-in mel function: 'renderLayerDisplayName', but first tries to see if it exists
def getRenderLayerDisplayName( layer_name ):
    if maya.mel.eval( 'exists renderLayerDisplayName' ):
        layer_name = maya.mel.eval( 'renderLayerDisplayName ' + layer_name )
    else:
        # renderLayerDisplayName doesn't exist, so we try to do it ourselves
        if layer_name == 'masterLayer':
            return layer_name

        if maya.cmds.objExists(layer_name) and maya.cmds.nodeType( layer_name ) == 'renderLayer':
            # Display name for default render layer
            if maya.cmds.getAttr( layer_name + '.identification' ) == 0:
                return 'masterLayer'

            # If Render Setup is used the corresponding Render Setup layer name should be used instead of the legacy render layer name.
            result = maya.cmds.listConnections( layer_name + '.msg', type='renderSetupLayer' )
            if result:
                return result[0]

    return layer_name

# remove_override_json_string is a json string consisting of a node as a key, with a list of attributes we want to unlock as the value
# ie. remove_override_json_string = '{ "defaultRenderGlobals": [ "animation", "startFrame", "endFrame" ] }'
def unlockRenderSetupOverrides( remove_overrides_json_string ):
    try:
        # Ensure we're in a version that HAS render setups
        import maya.app.renderSetup.model.renderSetup as renderSetup
    except ImportError:
        return

    # Ensure that the scene is actively using render setups and not the legacy layers
    if not maya.mel.eval( 'exists mayaHasRenderSetup' ) or not maya.mel.eval( 'mayaHasRenderSetup();' ):
        return

    remove_overrides = json.loads( remove_overrides_json_string )

    render_setup = renderSetup.instance()
    layers = render_setup.getRenderLayers()
    layers_to_unlock = [ layer for layer in layers if layer.name() != 'defaultRenderLayer' ]

    for render_layer in layers_to_unlock:
        print('Disabling Render Setup Overrides in "%s"' % render_layer.name())
        for collection in render_layer.getCollections():
            if type(collection) == maya.app.renderSetup.model.collection.RenderSettingsCollection:
                for override in collection.getOverrides():
                    if override.targetNodeName() in remove_overrides and override.attributeName() in remove_overrides[ override.targetNodeName() ]:
                        print( '    Disabling Override: %s.%s' % ( override.targetNodeName(), override.attributeName() ) )
                        override.setSelfEnabled( False )