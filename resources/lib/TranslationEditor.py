import sys
import xbmc
import xbmcgui
import MypicsDB as MPDB
import common

#_ = sys.modules[ "__main__" ].__language__


STATUS_LABEL    = 100
STATUS_LABEL2   = 101
BUTTON_OK       = 102
BUTTON_CANCEL   = 103
TAGS_LIST       = 120
CANCEL_DIALOG   = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_SELECT_ITEM = 7
ACTION_MOUSE_START = 100
ACTION_TAB         = 18
SELECT_ITEM = (ACTION_SELECT_ITEM, ACTION_MOUSE_START)

class TranslationEditor( xbmcgui.WindowXMLDialog ):
    
    def __init__( self, xml, cwd, default):
        xbmcgui.WindowXMLDialog.__init__(self)
    
    def onInit( self ):  
        self.setup_all()

    def setup_all( self ):

        self.getControl( STATUS_LABEL ).setLabel( common.getstring(30620) )
        self.getControl( STATUS_LABEL2 ).setLabel( common.getstring(30622) )
        self.getControl( BUTTON_OK ).setLabel( common.getstring(30621) )
        self.getControl( TAGS_LIST ).reset()
        
        TagTypesAndTranslation =  MPDB.getTagTypesForTranslation()

        for TagTypeAndTranslation in TagTypesAndTranslation:
            listitem = xbmcgui.ListItem( label=TagTypeAndTranslation[0], label2=TagTypeAndTranslation[1]) 
            self.getControl( TAGS_LIST ).addItem( listitem )

        self.setFocus( self.getControl( TAGS_LIST ) )
        self.getControl( TAGS_LIST ).selectItem( 0 )

     
    
    def onClick( self, controlId ):
        pass    

    def onFocus( self, controlId ):
        self.controlId = controlId

    def onAction( self, action ):
        #try:
            # Cancel
            if ( action.getId() in CANCEL_DIALOG or self.getFocusId() == BUTTON_CANCEL and action.getId() in SELECT_ITEM ):
                self.close()
            # Okay
            if ( self.getFocusId() == BUTTON_OK and action.getId() in SELECT_ITEM ):
                self.close()
            
            # Select or deselect item in list
            if ( action.getId() in SELECT_ITEM and self.getFocusId() == TAGS_LIST ):
                item = self.getControl( TAGS_LIST ).getSelectedItem()
                #pos  = self.getControl( TAGS_LIST ).getSelectedPosition()
                
                kb = xbmc.Keyboard(item.getLabel2(),  common.getstring(30623)%( common.smart_utf8(item.getLabel())), False)
                kb.doModal()
                if (kb.isConfirmed()):
                    item.setLabel2(kb.getText())
                    MPDB.setTranslatedTagType(common.smart_unicode(item.getLabel()), common.smart_unicode(item.getLabel2()))
                    self.getControl( TAGS_LIST ).setVisible(False)
                    self.getControl( TAGS_LIST ).setVisible(True)

                    
