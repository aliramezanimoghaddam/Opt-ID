package uk.ac.diamond.optid;

import org.eclipse.ui.IFolderLayout;
import org.eclipse.ui.IPageLayout;
import org.eclipse.ui.IPerspectiveFactory;
import org.eclipse.ui.IViewLayout;

public class IdSortPerspective implements IPerspectiveFactory {
	
	static final String ID = "uk.ac.diamond.optid.idSortPerspective";

	@Override
	public void createInitialLayout(IPageLayout layout) {
		String editorArea = layout.getEditorArea();
		layout.setEditorAreaVisible(true);
		
		/*
		IFolderLayout left = layout.createFolder("idDescForm", IPageLayout.LEFT, 0.3f, editorArea);
		left.addView("uk.ac.diamond.optid.idDescForm");
		IViewLayout vLayout = layout.getViewLayout("uk.ac.diamond.optid.idDescForm");
		vLayout.setCloseable(false);
		*/
		
		IFolderLayout leftFolder = layout.createFolder("leftFolder", IPageLayout.LEFT, 0.25f, editorArea);
		leftFolder.addView("uk.ac.diamond.optid.mainView");
		IViewLayout vLayout = layout.getViewLayout("uk.ac.diamond.optid.mainView");
		vLayout.setCloseable(false);
		
		IFolderLayout rightFolder = layout.createFolder("rightFolder", IPageLayout.RIGHT, 0.6f, IPageLayout.ID_EDITOR_AREA);
		rightFolder.addView("org.dawb.workbench.views.dataSetView");
		rightFolder.addView("org.dawb.workbench.plotting.views.toolPageView.2D");
		rightFolder.addView("org.dawb.common.ui.views.headerTableView");
		
		IFolderLayout bottomFolder = layout.createFolder("bottomFolder", IPageLayout.BOTTOM, 0.7f, IPageLayout.ID_EDITOR_AREA);
		bottomFolder.addView("org.eclipse.ui.views.ProgressView");
		bottomFolder.addView("org.eclipse.ui.console.ConsoleView");
	}

}